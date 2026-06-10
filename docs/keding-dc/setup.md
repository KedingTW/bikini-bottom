# 科定AI服務 (DC) — 伺服器設定文件

> Discord 伺服器，提供科定同事使用的專用 AI bot。
> 每個 bot 只做一件事，不閒聊、不跨業務。
> 新增 bot 請參考 [bot-setup-sop-keding-dc.md](./bot-setup-sop-keding-dc.md)

---

## 伺服器資訊

| 項目 | 值 |
|------|-----|
| 伺服器名稱 | 科定AI服務 |
| Guild ID | `1513867618899988480` |
| Agent 目錄 | `agents/keding-dc/` |
| K3s deployment 前綴 | `keding-dc-` |
| Secret | `keding-dc-secrets` |
| Entrypoint | `entrypoint-minimal.sh`（不做 NAS / steering / skills link） |
| Image | `bikini-bottom/agent:latest`（共用） |

---

## 頻道配置

| 頻道名稱 | Channel ID | 類型 | 用途 | 對應 Bot |
|---------|-----------|------|------|---------|
| 下單小幫手 | `1513867725242503168` | Forum | 訂單資料轉換 | order-transform |

---

## Bot 配置

### 下單小幫手 (order-transform)

| 項目 | 值 |
|------|-----|
| Bot ID | `1514058459585445888` |
| 身分組 ID | `1514059154002677944` |
| Agent 路徑 | `agents/keding-dc/order-transform/` |
| K3s Deployment | `k3s/deployments/keding-dc-order-transform.yaml` |
| Secret key (token) | `keding-dc-secrets.ORDER_TRANSFORM_BOT_TOKEN` |
| Secret key (kiro) | `keding-dc-secrets.ORDER_TRANSFORM_KIRO_KEY` |
| MCP | `sap-mcp`（ValidateProductCode） |
| Steering | `personality.md` + `order-rules.md` |

#### 使用規範

1. 頻道類型為**論壇 (Forum)**
2. 每位同事每日建立一則貼文，標題格式：`[姓名] 日期`
3. 第一則訊息 **@下單小幫手**，貼上轉換需求
4. 之後在同一 post 內**不需要 mention**，直接打字即可互動
5. 不會安排其他 bot 加入此頻道

#### config.toml 設定說明

```toml
[discord]
allowed_channels = ["1513867725242503168"]   # 只在下單小幫手論壇回應
allow_bot_messages = "none"                  # 不回應其他 bot（此頻道無其他 bot）
allowed_role_ids = ["1514059154002677944"]   # mention 身分組也觸發
allow_user_messages = "involved"             # 首次 mention 後，同 thread 內自動回

[pool]
max_sessions = 15                            # 最多 15 位同事同時使用
session_ttl_hours = 24                       # session 保持 24 小時
```

#### 行為模式

| 觸發方式 | 回應？ | 說明 |
|---------|--------|------|
| 新 post 首則 @下單小幫手 | ✅ | bot 被 involve 進 thread |
| 同 post 後續訊息（不 mention） | ✅ | involved 模式自動回 |
| 其他 post（沒 mention 過） | ❌ | bot 未被 involve |
| mention 身分組「下單小幫手」 | ✅ | allowed_role_ids |
| DM 私訊 bot | ❌ | allow_dm=false（預設） |

---

## 新增 Bot SOP

要在此伺服器加新 bot（如客訴 bot、HR bot），照以下步驟：

### 1. Discord 設定

1. Discord Developer Portal 建 Bot Application
2. 開啟 MESSAGE CONTENT INTENT、SERVER MEMBERS INTENT
3. 邀請 bot 加入「科定AI服務」伺服器
4. 建立該 bot 的身分組，開啟「允許任何人 @mention」
5. 建立對應的 Forum 頻道

### 2. Agent 目錄

```bash
cp -r agents/keding-dc/order-transform agents/keding-dc/<new-bot-name>
# 編輯：
#   config.toml — 改 allowed_channels、allowed_role_ids
#   .kiro/steering/personality.md — 改業務範圍
#   .kiro/steering/<rules>.md — 換成該業務的規則
#   .kiro/settings/mcp.json — 換需要的 MCP
sudo chown -R twkder:twkder agents/keding-dc/<new-bot-name>
```

### 3. K3s

```bash
cp k3s/deployments/keding-dc-order-transform.yaml k3s/deployments/keding-dc-<new-bot-name>.yaml
# 編輯：改 name、labels、secret key name、hostPath
# 在 keding-dc-secrets 加入新 bot 的 token + kiro key
kubectl apply -f k3s/deployments/keding-dc-<new-bot-name>.yaml
```

### 4. 文件更新

- 本文件加入新頻道 + bot 資訊
- `.env.example` 加入新變數
- `.env.new` 加入實際值

---

## 身分組對照表

| 身分組名稱 | Role ID | 對應 Bot |
|-----------|---------|---------|
| 下單小幫手 | `1514059154002677944` | order-transform |

---

## 與比奇堡的差異

| 項目 | 比奇堡 | 科定AI服務 |
|------|--------|-----------|
| 用途 | AI 開發團隊（通用 agent） | 專用 bot 給同事用 |
| 使用者 | 開發者（你） | 業務同事 |
| bot 性格 | 有（章魚哥、海綿寶寶...） | 無（專業、簡短） |
| 頻道類型 | 一般 text + forum | 全 forum（每 bot 一個） |
| allow_user_messages | mentions（要 @） | involved（首次 @ 後免 @） |
| NAS 掛載 | 需要（projects symlink） | 不需要 |
| Git commit | 會產出（規格文件、PR） | 不會（純對話） |
