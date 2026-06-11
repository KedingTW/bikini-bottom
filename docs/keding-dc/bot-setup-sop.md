# 新增 Bot SOP — 科定AI服務 (DC)

> 在「科定AI服務」DC 伺服器新增一個專用 bot 的完整步驟。
> 每個 bot 只做一件事，不閒聊、不跨業務。

---

## 前置條件

- Discord Developer Portal 帳號
- K3s cluster 存取權
- Host 上 `agents/keding-dc/` 目錄寫入權限（需 sudo chown）

---

## 步驟

### 1. Discord 設定

1. Discord Developer Portal → New Application → 命名（中文業務名即可）
2. Bot 頁面 → Reset Token → 記下 token
3. 開啟 Privileged Gateway Intents：
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT
4. OAuth2 → URL Generator → scopes: `bot` → permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `Use External Emojis`
5. 用產生的 URL 邀請 bot 加入「科定AI服務」伺服器
6. 在伺服器設定建立該 bot 的身分組，開啟「允許任何人 @mention」
7. 建立對應的 **Forum 頻道**

### 2. 建立 Agent 目錄

```bash
# 從模板複製
cp -r agents/keding-dc/order-transform agents/keding-dc/<new-bot-name>

# 修改以下檔案：
```

#### config.toml

```toml
[discord]
bot_token = "${DISCORD_BOT_TOKEN}"
allowed_channels = ["<FORUM_CHANNEL_ID>"]
allow_bot_messages = "none"
allowed_role_ids = ["<BOT_ROLE_ID>"]
allow_user_messages = "involved"
max_bot_turns = 100

[agent]
command = "kiro-cli"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent"
env = { KIRO_API_KEY = "${KIRO_API_KEY}" }
inherit_env = ["GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "KIRO_API_KEY"]

[pool]
max_sessions = 15
session_ttl_hours = 24

[reactions]
enabled = true
remove_after_reply = false

[reactions.emojis]
queued = "👀"
thinking = "🤔"
tool = "🔥"
coding = "📋"
web = "⚡"
done = "🆗"
error = "😱"

[reactions.timing]
debounce_ms = 700
stall_soft_ms = 10000
stall_hard_ms = 30000
done_hold_ms = 1500
error_hold_ms = 2500
```

#### .kiro/steering/personality.md

- 定義唯一職責
- 設定管理員（可訓練）vs 一般同事（只能用）
- 糾正紀錄機制（見下方「NAS 儲存」章節）
- 輸出風格：只輸出答案、不輸出解析
- 糾正流程：判斷 → 主動確認 → 確認後 append 寫入

#### .kiro/steering/<rules>.md

放該業務的規則文件。

#### .kiro/settings/mcp.json

只放該 bot 需要的 MCP server。

#### .openab/

```bash
echo '{}' > .openab/thread_map.json
echo '# 不需要排程' > .openab/cronjob.toml
```

### 3. Git init

```bash
git init agents/keding-dc/<new-bot-name>
git -C agents/keding-dc/<new-bot-name> commit --allow-empty -m "init"
```

### 4. 修正權限

```bash
sudo chown -R twkder:twkder agents/keding-dc/<new-bot-name>
```

> `twkder` = uid 1000 = 容器內 `agent` user。不做這步 kiro-cli 會因權限問題無法寫入。

### 5. 建 K3s Secret + Deployment

```bash
# 加入 token 到 keding-dc-secrets
kubectl get secret keding-dc-secrets -n bikini-bottom -o json | \
  python3 -c "
import json, sys, base64
d = json.load(sys.stdin)
d['data']['<NEW_BOT>_BOT_TOKEN'] = base64.b64encode(b'<TOKEN>').decode()
d['data']['<NEW_BOT>_KIRO_KEY'] = base64.b64encode(b'<KIRO_KEY>').decode()
json.dump(d, sys.stdout)
" | kubectl apply -f -
```

Deployment YAML（複製 `keding-dc-order-transform.yaml` 改名稱和路徑）：

關鍵差異點：
- `command: ["/usr/local/bin/entrypoint-keding-dc.sh"]`
- 不掛 `/opt/steering`、`/opt/skills`
- Secret 指向 `keding-dc-secrets`
- **必須掛載 `kd-share` volume**（見下方「NAS 儲存」章節）

### 6. 部署

```bash
kubectl apply -f k3s/deployments/keding-dc-<new-bot-name>.yaml
kubectl logs -f deployment/keding-dc-<new-bot-name> -n bikini-bottom
# 應看到：discord bot connected user=<bot名稱>
```

### 7. 文件更新

- `./setup.md` — 加入新頻道 + bot 資訊
- `.env.example` / `.env.new` — 加入新變數
- `k3s/kustomization.yaml` — 加入新 deployment

---

## NAS 儲存（kd-share）

科定DC 的 bot 共用一個 NAS 目錄作為持久化儲存，用於糾正紀錄、中間產出等需要跨 session 保留的檔案。

### 路徑對應

| Host / K3s | 容器內 | 說明 |
|------------|--------|------|
| `/mnt/kd-share` | `/mnt/kd-share` | NAS: `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/89.KedingDC` |

### 目錄結構

```
/mnt/kd-share/
├── agents/
│   ├── order-transform/
│   │   └── correction-logs/    ← cl-{session_id}.log
│   └── <new-bot-name>/
│       └── ...                 ← 各 bot 自訂子目錄
└── shared/                     ← 跨 bot 共用資源（未來擴充）
```

### 新 bot 需要做的

1. **建立 NAS 子目錄**

```bash
# 本地開發機（透過 gvfs）
mkdir -p "/run/user/1002/gvfs/smb-share:server=192.168.1.218,share=kd共用/18_各部門共享區/21_系統開發課/89.KedingDC/agents/<new-bot-name>"

# 或在 K3s host 上
mkdir -p /mnt/kd-share/agents/<new-bot-name>
```

2. **Deployment YAML 加入 volume**

```yaml
          volumeMounts:
            - name: config
              mountPath: /etc/openab/config.toml
              readOnly: true
            - name: agent-home
              mountPath: /home/agent
            - name: kd-share              # ← 新增
              mountPath: /mnt/kd-share    # ← 新增
      volumes:
        - name: config
          hostPath:
            path: /home/kdprogramer/Projects/bikini-bottom/agents/keding-dc/<new-bot-name>/config.toml
            type: File
        - name: agent-home
          hostPath:
            path: /home/kdprogramer/Projects/bikini-bottom/agents/keding-dc/<new-bot-name>
            type: Directory
        - name: kd-share                  # ← 新增
          hostPath:                       # ← 新增
            path: /mnt/kd-share           # ← 新增
            type: DirectoryOrCreate       # ← 新增
```

3. **Steering 中使用 NAS 路徑**

糾正紀錄或任何需要持久化的檔案，寫入路徑統一為：

```
/mnt/kd-share/agents/<bot-name>/<用途子目錄>/<filename>
```

規則：
- **使用 fs_append 寫入，不用 fs_write**（避免併發覆蓋）
- 檔名帶 session_id（如 `cl-{session_id}.log`），每個 session 獨立檔案
- **不要寫在 `/home/agent/`**（session 結束後可能被清理，且多 session 會衝突）

### Host 掛載（已在 k3s-setup.sh 處理）

```bash
# fstab 設定（k3s-setup.sh 會自動加入）
//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/89.KedingDC /mnt/kd-share cifs credentials=/etc/nas-credentials,file_mode=0777,dir_mode=0777,vers=3.0,iocharset=utf8,echo_interval=10,_netdev,x-systemd.automount 0 0
```

---

## 與比奇堡 SOP 的差異

| 項目 | 比奇堡 | 科定DC |
|------|--------|--------|
| Entrypoint | `entrypoint-wrapper.sh` | `entrypoint-keding-dc.sh` |
| NAS mount | `/mnt/nas`（88.BikiniBottom） | `/mnt/kd-share`（89.KedingDC） |
| Shared steering | 需要（/opt/steering） | 不需要 |
| Shared skills | 需要（/opt/skills） | 不需要 |
| working_dir | `/home/agent/projects`（NAS） | `/home/agent` |
| 持久化檔案 | `/nas/agents/<name>/projects/` | `/mnt/kd-share/agents/<name>/` |
| allow_user_messages | `mentions`（要 @） | `involved`（首次 @ 後免 @） |
| Git commit | 會（規格/PR） | 不會（純對話） |
| 角色個性 | 有（章魚哥、海綿寶寶...） | 無（專業簡短） |
| 權限控制 | 無（團隊內部） | 有（管理員 vs 一般同事） |
