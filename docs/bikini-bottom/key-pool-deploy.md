# Key Pool — 正式環境部署指南

> 最後更新：2026-07-23
> 前置閱讀：[Key Pool 機制說明](key-pool.md)

---

## ⚠️ 部署前注意事項

1. **不要在正式環境直接測試** — 先在測試環境驗證通過再上正式
2. **部署過程中 agent 會有短暫中斷** — rollout restart 期間該 agent 無法回應（約 30 秒）
3. **建議逐一切換 agent** — 不要一次全部改，先切 1~2 個驗證，確認沒問題再全部切
4. **舊的 `kiro-api-keys` Secret 先保留不刪** — 確認穩定運行一週後再清理，方便回滾
5. **Key 值不要出現在 Discord / commit message / 任何公開場所**

---

## 部署順序

```
Phase 1: 準備（不影響現有服務）
  ↓
Phase 2: Admin Backend 部署（新增 API，不影響 agent）
  ↓
Phase 3: Agent 逐一切換（開始用 key pool）
  ↓
Phase 4: 驗證 & 清理
```

---

## Phase 1: 準備

### 1.1 確認 Key 清單

準備要放入 pool 的 key：

| key_name | 用途 | priority |
|----------|------|----------|
| POOL_01 | 主要使用 | 1 |
| POOL_02 | 備援 1 | 2 |
| POOL_03 | 備援 2 | 3 |

> ⚠️ priority 數字小的會先被消耗。建議把目前正在用的 key 設為 priority 1。

### 1.2 確認告警頻道

正式環境告警發到哪個 Discord 頻道？

- 預設：`1493802266296188988`
- 如需更改：部署時在 admin deployment YAML 設定 `KEY_POOL_ALERT_CHANNEL` 環境變數

### 1.3 確認 admin pod 能連到 Discord API

Admin pod 需要 `DISCORD_ADMIN_BOT_TOKEN` 才能發告警。確認 admin deployment 已有此 env（正式環境應已存在）。

---

## Phase 2: Admin Backend 部署

### 2.1 切換到 key-pool branch 並 build

```bash
cd /path/to/bikini-bottom
git checkout patrick_20260721_key-pool-coordinator  # 或 merge 到 master 後用 master
```

### 2.2 Build Admin Image

```bash
sudo docker build -f services/admin/Dockerfile -t bikini-bottom/admin:latest services/admin/
sudo k3s ctr images import <(sudo docker save bikini-bottom/admin:latest)
```

### 2.3 確認 Admin Deployment YAML 的環境變數

檢查 `k3s/deployments/admin.yaml`，確認有以下 env（如需覆蓋預設值才加）：

```yaml
# 可選 — 只有要覆蓋預設值時才加
- name: KEY_POOL_ALERT_CHANNEL
  value: "1493802266296188988"      # 告警頻道（預設值，不改可不加）
- name: KEY_POOL_USAGE_INTERVAL
  value: "1"                         # 排程間隔小時（預設 1）
```

### 2.4 Restart Admin Pod

```bash
kubectl rollout restart deployment/admin -n bikini-bottom
kubectl rollout status deployment/admin -n bikini-bottom
```

### 2.5 確認 Auto-Migrate 建表成功

```bash
kubectl logs deployment/admin -n bikini-bottom | grep "key_pool"
```

應該看到類似：
```
[key_pool] Tables initialized
[key_pool] Usage scheduler started (interval: 1h)
```

### 2.6 插入 Key 資料

透過 phpMyAdmin 或 kubectl exec 進 MySQL：

```bash
kubectl exec -it deployment/admin-mysql -n bikini-bottom -- mysql -u admin -p admin_dashboard
```

```sql
INSERT INTO key_pool (key_name, key_value, priority, enabled, note) VALUES
('POOL_01', '你的_key_值_01', 1, 1, '主要使用 - 帳號備註'),
('POOL_02', '你的_key_值_02', 2, 1, '備援 1 - 帳號備註'),
('POOL_03', '你的_key_值_03', 3, 1, '備援 2 - 帳號備註');
```

> ⚠️ key_value 是機敏資料，操作完後清除 shell history（`history -c`）。

### 2.7 驗證 Admin API

```bash
# 從 admin pod 內部或同 cluster 測試
curl http://admin:8501/api/key-pool/state | jq
```

確認回傳：
- `total_keys` = 你插入的數量
- `available_keys` = 同上
- `exhausted_keys` = 0

---

## Phase 3: Agent 切換

### 3.1 Build Agent Image

```bash
sudo docker build -f Dockerfile.bikini-bottom -t bikini-bottom/agent:latest .
sudo k3s ctr images import <(sudo docker save bikini-bottom/agent:latest)
```

### 3.2 確認 KEY_POOL_URL

正式環境 agent pod 使用 `hostNetwork: true`，DNS 可能走 host 不走 CoreDNS。

確認 admin service 的 ClusterIP：
```bash
kubectl get svc admin -n bikini-bottom -o jsonpath='{.spec.clusterIP}'
```

`KEY_POOL_URL` 設為：`http://<ClusterIP>:8501/api/key-pool`

### 3.3 修改 Agent Deployment YAML

以 bob 為例（`k3s/deployments/bikini-bottom/bob.yaml`）：

**移除：**
```yaml
# 刪除這段
- name: KIRO_API_KEY
  valueFrom:
    secretKeyRef:
      name: kiro-api-keys
      key: BOB
```

**新增：**
```yaml
# 加入這段
- name: KEY_POOL_URL
  value: "http://<admin-clusterip>:8501/api/key-pool"
```

> ⚠️ `AGENT_NAME` 已存在，不用額外加。

### 3.4 修改 Agent config.toml

每個 agent 的 `config.toml`：

```diff
 [agent]
-command = "kiro-cli"
+command = "kiro-key-wrap"
 args = ["acp", "--trust-all-tools"]
 working_dir = "/home/agent"
-env = { KIRO_API_KEY = "${KIRO_API_KEY}" }
-inherit_env = ["GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "KIRO_API_KEY"]
+env = {}
+inherit_env = ["GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "KEY_POOL_URL", "AGENT_NAME"]
```

### 3.5 逐一 Rollout（建議順序）

先切一個不重要的 agent 驗證：

```bash
# 第一批：先切一個驗證
kubectl rollout restart deployment/conch -n bikini-bottom
# 在 Discord mention 神奇海螺，確認能正常回應

# 確認沒問題後切其他
kubectl rollout restart deployment/bob -n bikini-bottom
kubectl rollout restart deployment/patrick -n bikini-bottom
kubectl rollout restart deployment/squidward -n bikini-bottom
# ...逐一切換
```

### 3.6 每切一個都驗證

1. 在 Discord mention 該 agent，確認能正常回應
2. 查 admin 的 pick_log 確認有紀錄：
```bash
curl http://admin:8501/api/key-pool/state | jq '.current_key'
```

---

## Phase 3.5: 科定 DC Agent（如需要）

科定 DC 的 agent（`keding-dc/order-transform`, `keding-dc/order-teacher`）目前用不同的 secret key field。如果也要加入 pool：

1. 確認這些 agent 的 key 也放入 `key_pool` 表
2. 修改對應 deployment YAML + config.toml
3. 或者先不動，保持獨立 key — 它們用量可能不大

---

## Phase 4: 驗證 & 清理

### 4.1 全面驗證

- [ ] 所有 agent 都能正常回應 Discord 訊息
- [ ] `GET /api/key-pool/state` 顯示正確（pick_count 有增加）
- [ ] Usage 排程正常跑（`last_usage_checked_at` 有更新）
- [ ] 手動 `POST /api/key-pool/check-usage` 能查到用量
- [ ] 模擬全耗盡（手動 mark 所有 key）→ 503 + fallback key 行為正確
- [ ] 解除 mark → 下一個 session 恢復正常

### 4.2 告警驗證

手動把某把 key 的 `last_usage_percent` 設成 100：
```sql
UPDATE key_pool SET last_usage_percent = 100 WHERE key_name = 'POOL_01';
```
然後觸發 `POST /api/key-pool/check-usage`，確認收到 Discord 告警。
驗證完記得改回來。

### 4.3 清理（穩定運行一週後）

- [ ] 移除 `kiro-api-keys` Secret 中各 agent 的個別 key field（BOB, PATRICK, ...）
- [ ] 移除 deployment YAML 中已刪除的舊 env 引用（如果有殘留）
- [ ] 確認 `kiro-api-keys` Secret 可以完全刪除（所有 agent 都用 pool 了）

---

## 回滾方案

如果出問題，30 秒內可回滾：

1. Agent config.toml 改回：
```toml
command = "kiro-cli"
env = { KIRO_API_KEY = "${KIRO_API_KEY}" }
inherit_env = ["...", "KIRO_API_KEY"]
```

2. Deployment YAML 恢復 `KIRO_API_KEY` env（指向 `kiro-api-keys` Secret）

3. Rollout restart：
```bash
kubectl rollout restart deployment/<agent-name> -n bikini-bottom
```

> 前提：`kiro-api-keys` Secret 沒有被刪除（Phase 4.3 之前都還在）。

---

## 需要切換的 Agent 清單（比奇堡）

| Agent | Deployment | config.toml 路徑 |
|-------|------------|------------------|
| bob | `k3s/deployments/bikini-bottom/bob.yaml` | `agents/bikini-bottom/bob/config.toml` |
| patrick | `k3s/deployments/bikini-bottom/patrick.yaml` | `agents/bikini-bottom/patrick/config.toml` |
| squidward | `k3s/deployments/bikini-bottom/squidward.yaml` | `agents/bikini-bottom/squidward/config.toml` |
| sandy | `k3s/deployments/bikini-bottom/sandy.yaml` | `agents/bikini-bottom/sandy/config.toml` |
| gary | `k3s/deployments/bikini-bottom/gary.yaml` | `agents/bikini-bottom/gary/config.toml` |
| conch | `k3s/deployments/bikini-bottom/conch.yaml` | `agents/bikini-bottom/conch/config.toml` |
| puff | `k3s/deployments/bikini-bottom/puff.yaml` | `agents/bikini-bottom/puff/config.toml` |
| pearl | `k3s/deployments/bikini-bottom/pearl.yaml` | `agents/bikini-bottom/pearl/config.toml` |
| larry | `k3s/deployments/bikini-bottom/larry.yaml` | `agents/bikini-bottom/larry/config.toml` |
| mermaid-man | `k3s/deployments/bikini-bottom/mermaid-man.yaml` | `agents/bikini-bottom/mermaid-man/config.toml` |

---

## 常見問題

### Agent 出現 🚫 反應

可能原因：
- `KEY_POOL_URL` 設錯（確認 ClusterIP 正確）
- Admin pod 掛了（`kubectl get pod -l app=admin -n bikini-bottom`）
- `AGENT_NAME` 沒設（pick_log 會顯示 "unknown"）

### Agent 出現 "Connection Lost"

可能原因：
- 所有 key 都 exhausted 且 503 fallback 的 key 也真的不能用
- kiro-cli 本身啟動失敗（key 無效）

### 告警沒收到

確認：
- `DISCORD_ADMIN_BOT_TOKEN` env 有設定
- `KEY_POOL_ALERT_CHANNEL` 頻道 ID 正確
- Admin pod 能連到 Discord API（外網）

### 排程沒跑

確認：
- Admin pod log 有 `Usage scheduler started`
- 如果顯示 `kiro-cli not found`：admin image 沒有正確安裝 kiro-cli，需要 rebuild
