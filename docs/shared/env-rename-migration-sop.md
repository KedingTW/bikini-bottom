# .env 重新命名遷移 SOP

> 將 `.env` 變數從舊命名（如 `DISCORD_BOT_TOKEN_BOB`）遷移到新命名（如 `BIKINI_BOTTOM_BOB_BOT_TOKEN`）。
> 新命名規則：`<GROUP>_<AGENT>_<PURPOSE>`

---

## 前置作業（已完成）

- [x] `.env.example` 已更新為新命名格式
- [x] `.env.new` 已從現有 `.env` 產生，值已對應填入
- [x] `KEDING_DC_ORDER_TRANSFORM_BOT_TOKEN` 待填入（DC bot token）

---

## 遷移步驟（下班時間執行，預計 10 分鐘）

### 1. 確認 .env.new 值齊全

```bash
# 檢查空值
grep '=$' .env.new
# 應只剩 CONCH_ADMIN_IDS、CONCH_OPERATOR_ROLE_IDS（原本就空）
# 和 REDMINE / DASHBOARD（原本就沒用）
```

### 2. 備份並切換 .env

```bash
cp .env .env.bak.$(date +%Y%m%d)
mv .env.new .env
```

### 3. 更新 K3s Secrets

需要刪除舊 secret 並建新的。key name 變了：

```bash
# 刪除舊 secret
kubectl delete secret discord-tokens kiro-api-keys -n bikini-bottom

# 建新 secret — discord tokens
kubectl create secret generic bikini-bottom-discord-tokens -n bikini-bottom \
  --from-literal=BOB="$(grep BIKINI_BOTTOM_BOB_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=PATRICK="$(grep BIKINI_BOTTOM_PATRICK_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=PUFF="$(grep BIKINI_BOTTOM_PUFF_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=SQUIDWARD="$(grep BIKINI_BOTTOM_SQUIDWARD_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=SANDY="$(grep BIKINI_BOTTOM_SANDY_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=GARY="$(grep BIKINI_BOTTOM_GARY_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=CONCH="$(grep BIKINI_BOTTOM_CONCH_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=PEARL="$(grep BIKINI_BOTTOM_PEARL_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=LARRY="$(grep BIKINI_BOTTOM_LARRY_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=MERMAID_MAN="$(grep BIKINI_BOTTOM_MERMAID_MAN_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=KAREN="$(grep BIKINI_BOTTOM_KAREN_BOT_TOKEN .env | cut -d= -f2-)"

# 建新 secret — kiro api key（全員共用一把）
kubectl create secret generic bikini-bottom-kiro-key -n bikini-bottom \
  --from-literal=KIRO_API_KEY="$(grep BIKINI_BOTTOM_KIRO_API_KEY .env | cut -d= -f2-)"

# 建新 secret — 科定DC
kubectl create secret generic keding-dc-secrets -n bikini-bottom \
  --from-literal=ORDER_TRANSFORM_BOT_TOKEN="$(grep KEDING_DC_ORDER_TRANSFORM_BOT_TOKEN .env | cut -d= -f2-)" \
  --from-literal=ORDER_TRANSFORM_KIRO_KEY="$(grep KEDING_DC_ORDER_TRANSFORM_KIRO_KEY .env | cut -d= -f2-)"
```

### 4. 更新 K3s Deployments

所有 deployment YAML 裡的 `secretKeyRef` 要改指向新 secret name。

**比奇堡 deployments 改動（以 bob.yaml 為例）：**

```yaml
# 舊
- name: DISCORD_BOT_TOKEN
  valueFrom:
    secretKeyRef:
      name: discord-tokens
      key: BOB
- name: KIRO_API_KEY
  valueFrom:
    secretKeyRef:
      name: kiro-api-keys
      key: BOB

# 新
- name: DISCORD_BOT_TOKEN
  valueFrom:
    secretKeyRef:
      name: bikini-bottom-discord-tokens
      key: BOB
- name: KIRO_API_KEY
  valueFrom:
    secretKeyRef:
      name: bikini-bottom-kiro-key
      key: KIRO_API_KEY
```

**科定DC deployment (`keding-dc-order-transform.yaml`) 已寫好指向 `keding-dc-secrets`。**

### 5. 搬遷 agents 目錄（比奇堡）

```bash
mkdir -p agents/bikini-bottom
# 搬所有比奇堡 agent
for agent in bob patrick puff squidward sandy conch pearl larry mermaid-man; do
  sudo mv agents/$agent agents/bikini-bottom/
done

# 更新所有 deployment 的 hostPath
sed -i 's|/agents/bob|/agents/bikini-bottom/bob|g' k3s/deployments/bob.yaml
# ... 對每個 agent 做同樣的事（或用 script）
```

### 6. Apply 並重啟

```bash
kubectl apply -k k3s/
kubectl rollout restart deployment -n bikini-bottom
```

### 7. 驗證

```bash
# 全部 pod Running
kubectl get pods -n bikini-bottom

# 抽檢一個 bot 的 log
kubectl logs -f deployment/bob -n bikini-bottom --tail=5
# 應看到 discord bot connected
```

---

## Rollback

如果出問題：

```bash
mv .env .env.failed
cp .env.bak.YYYYMMDD .env
# secret 不用改回（舊的還在，沒刪的話）
# deployment revert: git checkout k3s/deployments/
kubectl apply -k k3s/
kubectl rollout restart deployment -n bikini-bottom
```

---

## 命名對照表（新 ← 舊）

| 新名稱 | 舊名稱 | 說明 |
|--------|--------|------|
| `BIKINI_BOTTOM_KIRO_API_KEY` | `KIRO_API_KEY_BOB`（全員同值） | 共用一把 |
| `BIKINI_BOTTOM_BOB_BOT_TOKEN` | `DISCORD_BOT_TOKEN_BOB` | Bot token |
| `BIKINI_BOTTOM_CHANNEL_KRUSTY_KRAB` | `CHANNEL_KRUSTY_KRAB` | Channel ID |
| `BIKINI_BOTTOM_GUILD_ID` | `DISCORD_GUILD_ID` | Guild ID |
| `KEDING_DC_ORDER_TRANSFORM_BOT_TOKEN` | (新) | DC 下單小幫手 |
| `KEDING_DC_ORDER_TRANSFORM_KIRO_KEY` | (新，同值) | DC 下單小幫手 Kiro key |
| `KEDING_WECOM_ORDER_TRANSFORM_*` | `ORDER_TRANSFORM_WECOM_*` | WeCom 下單小幫手 |

---

## 注意事項

- **docker-compose.yml** 也要同步改 `${VAR_NAME}`（如果還保留 docker compose 模式）
- **admin backend** 的 `app.py` 如有直接讀 env 的地方要檢查
- **slash-bot** 的 env 讀取也要改
- 建議全部改完後跑一次 `grep -r 'DISCORD_BOT_TOKEN_\|KIRO_API_KEY_\|CHANNEL_' k3s/ services/ docker-compose.yml` 確認沒殘留
