# Kiro API Key Pool — 交接文件

## 📋 背景

### 痛點
- 所有 bot（10 隻）共用同一把 Kiro API Key，每月 10,000 credits 不夠用
- 撞牆時需手動切換 API Key → 全部 bot 重啟 → 服務中斷
- 無法自動偵測額度耗盡，靠人工觀察

### 方案
借鑑 [kiro-multi](https://github.com/wangyuyan-agent/kiro-multi) 的 wrapper + pool 機制，  
簡化為 API Key 模式，做成 `kiro-key-wrap`，在每個 session 啟動時自動從 pool 中選一把可用的 key。

---

## 🏗️ 架構

```
openab → spawn "kiro-key-wrap acp --trust-all-tools"
                    │
                    ├─ flock 加鎖讀 state.json
                    ├─ round-robin 選一把非 exhausted 的 key
                    ├─ KIRO_API_KEY=$selected exec kiro-cli
                    ├─ session 結束後 grep stderr
                    └─ 偵測 quota/rate-limit → 標記 exhausted → 下次不選它
```

### 容器內路徑

| 路徑 | 來源 | 用途 |
|------|------|------|
| `/usr/local/bin/kiro-key-wrap` | Dockerfile COPY | Wrapper script |
| `/usr/local/lib/kiro-pool/pick.py` | Dockerfile COPY | 選 key 邏輯 |
| `/usr/local/lib/kiro-pool/mark_exhausted.py` | Dockerfile COPY | 標記撞牆 |
| `/etc/kiro-pool/keys.json` | ConfigMap `kiro-key-pool` | Key 清單（唯讀） |
| `/data/kiro-pool/state.json` | hostPath 共享 | 輪替狀態（所有 pod 共用） |
| `/data/kiro-pool/state.lock` | hostPath 共享 | flock 檔案 |
| `/data/kiro-pool/logs/` | hostPath 共享 | 撞牆 stderr log |

### k3s 節點對應

```
/home/kdprogramer/kiro-pool/        ← hostPath（DirectoryOrCreate）
├── state.json
├── state.lock
└── logs/
```

---

## 📁 本次新增/修改的檔案

### 新增

| 檔案 | 說明 |
|------|------|
| `services/kiro-key-pool/kiro-key-wrap` | Wrapper shell script |
| `services/kiro-key-pool/pick.py` | Round-robin pick 邏輯 |
| `services/kiro-key-pool/mark_exhausted.py` | 標記 key exhausted |
| `services/kiro-key-pool/keys.example.json` | keys.json 範例 |
| `services/kiro-key-pool/README.md` | 操作說明 |
| `k3s/configmaps/kiro-key-pool.yaml` | ConfigMap manifest |
| `docs/kiro-key-pool-handover.md` | 本文件 |

### 修改（僅 bob 作為範本）

| 檔案 | 改動 |
|------|------|
| `Dockerfile` | 加入 COPY kiro-key-wrap + pick.py + mark_exhausted.py |
| `agents/bob/config.toml` | command → `kiro-key-wrap`，移除 KIRO_API_KEY env |
| `k3s/deployments/bob.yaml` | 移除 KIRO_API_KEY secretRef，加 ConfigMap + hostPath mount |

---

## 🚀 部署步驟（你需要做的）

### 1. 其他 bot 同樣修改

以下 bot 需要做跟 bob 一樣的改動：

**config.toml** — 所有 bot 都改：
```toml
[agent]
command = "kiro-key-wrap"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent/projects"
env = {}
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AGENT_NAME"]
```

**k3s deployment** — 所有 bot 都加：
```yaml
# 移除這段：
- name: KIRO_API_KEY
  valueFrom:
    secretKeyRef:
      name: kiro-api-keys
      key: XXX

# volumeMounts 加：
- name: kiro-key-pool
  mountPath: /etc/kiro-pool
  readOnly: true
- name: kiro-pool-state
  mountPath: /data/kiro-pool

# volumes 加：
- name: kiro-key-pool
  configMap:
    name: kiro-key-pool
- name: kiro-pool-state
  hostPath:
    path: /home/kdprogramer/kiro-pool
    type: DirectoryOrCreate
```

需要改的 bot：`patrick, larry, conch, sandy, squidward, puff, gary, pearl, mermaid-man`

### 2. 設定 keys.json

編輯 `k3s/configmaps/kiro-key-pool.yaml`，把你的 key 填進去：

```json
[
  {
    "id": "power_1",
    "key": "ksk_你的第一把Key",
    "tier": "power",
    "note": "主帳號"
  },
  {
    "id": "power_2",
    "key": "ksk_你的第二把Key",
    "tier": "power",
    "note": "備用帳號"
  }
]
```

### 3. Build & Deploy

```bash
# Build image
docker build -t bikini-bottom/agent:latest .

# Apply ConfigMap
kubectl apply -f k3s/configmaps/kiro-key-pool.yaml

# Rollout（可逐一，先 bob 測試）
kubectl rollout restart deployment/bob -n bikini-bottom

# 確認 ok 後全部
kubectl rollout restart deployment -l type=agent -n bikini-bottom
```

### 4. 驗證

```bash
# 在 k3s node 上檢查 state.json
cat /home/kdprogramer/kiro-pool/state.json | python3 -m json.tool

# 看 bob pod 的 stderr 有沒有 [kiro-key-wrap] picked key
kubectl logs deployment/bob -n bikini-bottom | grep kiro-key-wrap
```

---

## 🔧 日常操作

### 加新 key

```bash
kubectl edit configmap kiro-key-pool -n bikini-bottom
# 在 keys.json 陣列加一筆，存檔即生效（下個新 session 會用到）
```

### 查看 pool 狀態

```bash
# SSH 到 k3s node
cat /home/kdprogramer/kiro-pool/state.json | python3 -m json.tool

# 看哪些 key exhausted
python3 -c "
import json
state = json.load(open('/home/kdprogramer/kiro-pool/state.json'))
for kid, ks in state.get('keys', {}).items():
    status = '❌ EXHAUSTED' if ks.get('exhausted') else '✅ OK'
    print(f'  {kid}: {status}  picks={ks.get(\"pick_count\",0)}')
"
```

### 手動解凍 key（如果需要）

```bash
python3 -c "
import json
state = json.load(open('/home/kdprogramer/kiro-pool/state.json'))
state['keys']['power_1']['exhausted'] = False
state['keys']['power_1']['resets_at'] = None
json.dump(state, open('/home/kdprogramer/kiro-pool/state.json', 'w'), indent=2)
print('Done')
"
```

### 查看撞牆 log

```bash
ls -lt /home/kdprogramer/kiro-pool/logs/ | head -5
cat /home/kdprogramer/kiro-pool/logs/<latest>.log
```

---

## ⚠️ 注意事項

1. **state.json 是所有 bot pod 共用的**（透過 hostPath），flock 確保不會並發寫壞
2. **keys.json 是 ConfigMap**，修改後 k8s 會自動同步到 pod（有 1~2 分鐘延遲）
3. **進行中的 session 不會被影響**——key 在 session 開始時決定，中途不會換
4. **撞牆偵測是被動的**——只有 session 結束時才檢查 stderr，不是即時的
5. **月初自動解凍**——pick.py 在選 key 時會檢查 resets_at，如果已過就自動清除 exhausted

---

## 🔮 後續可選強化

- [ ] 整合到 slash-bot：加 `/pool-status` 指令在 Discord 看 key 狀態
- [ ] 整合 Athena usage 查詢：定期更新 state.json 中各 key 的 usage%
- [ ] 考慮縮短 session_ttl_hours（24h → 8h）讓 key rotation 更靈敏
- [ ] wecom-bot 也改用 pool（目前有獨立的 KIRO_API_KEY_WECOM_BOT）
