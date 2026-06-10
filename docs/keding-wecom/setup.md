# WeCom Bot on Zeabur — 部署指南

> ⚠️ **狀態：暫停** — WeCom 缺乏表情反應機制，使用者體驗不佳，已改用 Discord 方式（科定AI服務 DC）。
> 本文件保留作為未來重啟參考。Zeabur project `kd-wecom` 仍在線（gateway 跑著），隨時可重啟。

> 把 OpenAB Gateway 部署到 Zeabur（雲端 HTTPS 終端），地端 K3s 跑 wecom-bot agent（連 MCP）。
> 一個業務 = 一個 WeCom 應用 + 一個 Zeabur gateway + 一個地端 wecom-bot。

---

## 架構（最終樣貌）

```
WeCom 雲端 ──HTTPS──▶  Zeabur gateway-<name>     ◀══wss══  地端 K3s wecom-bot-<name>  ──▶  MCP（內網）
   (1 個應用)            (image: openab-gateway)            (kiro-cli + skill + steering)
                          stateless 純轉發                   有狀態，session per user
```

**為何分兩段**：
- gateway 需要 HTTPS + 公網（WeCom 強制） → 上 Zeabur 最便宜（$5/mo 帳號級）
- wecom-bot 需要連內網 MCP、需要持久化 home dir → 留在地端 K3s
- ws 是地端「主動 outbound」連雲端，不需要任何 inbound port 開放

---

## 角色分工

| 元件 | 位置 | 職責 |
|---|---|---|
| WeCom 應用 | 企業微信管理後台 | 提供 corp_id / agent_id / secret / token / aes_key |
| Zeabur gateway | Zeabur cloud | HTTPS 收 webhook、解密、ws 派發給 agent |
| `wecom-bot-<name>` agent | 地端 K3s | 跑 kiro-cli，照 steering/skill/MCP 回應使用者 |
| `services/zeabur-gateway/bots/<name>.yaml` | repo | 單一事實來源，串起上述三者 |

---

## 第一次部署（以 `order` 為例）

> 前提：已在 .env 填好 Zeabur API key、ikd.ink DNS 管理權、企業微信管理員權限。

### 1. 確認本機設定齊全

```bash
python services/zeabur-gateway/scripts/list-bots.py
# 應該看到 order 是 enabled

python services/zeabur-gateway/scripts/check-env.py --bot order-transform
# 確認 5 個 ORDER_TRANSFORM_WECOM_* 都已填
```

### 2. 印出 Zeabur 部署步驟

```bash
python services/zeabur-gateway/scripts/print-deploy-instructions.py order-transform
```

跟著印出的步驟在 Zeabur Dashboard 操作：

#### 2a. 建 Project + Service

- Project: `bikini-bottom`
- Service:
  - Name: `gateway-order-transform`
  - Source: **Prebuilt Image**
  - Image: `ghcr.io/openabdev/openab-gateway:latest`
  - Exposed Port: `8080`

#### 2b. 設環境變數（Variables 分頁）

| Gateway 內變數 | 從 .env 哪一行複製 |
|---|---|
| `WECOM_CORP_ID` | `ORDER_TRANSFORM_WECOM_CORP_ID` |
| `WECOM_AGENT_ID` | `ORDER_TRANSFORM_WECOM_AGENT_ID` |
| `WECOM_SECRET` | `ORDER_TRANSFORM_WECOM_SECRET` |
| `WECOM_TOKEN` | `ORDER_TRANSFORM_WECOM_TOKEN` |
| `WECOM_ENCODING_AES_KEY` | `ORDER_TRANSFORM_WECOM_ENCODING_AES_KEY` |

> 安全建議：另外加一個 `GATEWAY_WS_TOKEN`（隨機 32+ 字元），地端 agent config 對應加 `auth_token`，避免任何人都能連你的 gateway。

#### 2c. 綁 Domain

- Zeabur 會給一個預設 domain（如 `gateway-order-transform-xxx.zeabur.app`），先記下
- 在 ikd.ink DNS 新增一筆：
  ```
  order-transform.ikd.ink.  CNAME  gateway-order-transform-xxx.zeabur.app.
  ```
- 回 Zeabur Service → Domains → 加 `order-transform.ikd.ink`，等 SSL 簽發完成（通常 < 1 分鐘）

### 3. 設定 WeCom 後台

到企業微信管理後台 → 你的訂單轉換應用 → 接收消息 → 設置 API 接收：

- URL: `https://order-transform.ikd.ink/webhook/wecom`
- Token: 對應 `.env` 的 `ORDER_TRANSFORM_WECOM_TOKEN`
- EncodingAESKey: 對應 `.env` 的 `ORDER_TRANSFORM_WECOM_ENCODING_AES_KEY`

點「保存」。Zeabur gateway 會收到 echostr 驗證，正確會顯示「保存成功」。

### 4. 部署地端 wecom-bot-order-transform

```bash
# build agent image（如果尚未 build）
docker build -t bikini-bottom/agent:latest .
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -

# 在 K3s 加 KIRO_API_KEY
kubectl edit secret kiro-api-keys -n bikini-bottom
# 加一行（值用 base64 編碼）：
#   WECOM_BOT_ORDER: <base64 encoded KIRO_API_KEY_WECOM_BOT_ORDER>

# 部署
kubectl apply -f k3s/deployments/wecom-bot-order-transform.yaml

# 看 logs 確認 ws 連線成功
kubectl logs -f deployment/wecom-bot-order-transform -n bikini-bottom
# 應該看到類似：connected to wss://order-transform.ikd.ink/ws
```

### 5. 測試

在企業微信中打開「訂單轉換」應用，傳一則訊息：

```
P181G. 2x8皮=2。 3mm. =7
```

bot 應回覆品號/數量/對花備註三段。

---

## 新增第二個 bot（以 `complaint` 為例）

照 [services/zeabur-gateway/README.md](../../services/zeabur-gateway/README.md) 的「新增一個 wecom bot 的完整流程」走：

1. `cp services/zeabur-gateway/bots/_template.yaml services/zeabur-gateway/bots/complaint.yaml` → 編輯
2. `cp -r agents/wecom-bot-order-transform/ agents/wecom-bot-complaint/` → 改 personality/order-rules/mcp/config
3. 在 `.env` 加 5 個 `COMPLAINT_WECOM_*` + `KIRO_API_KEY_WECOM_BOT_COMPLAINT`
4. `python services/zeabur-gateway/scripts/check-env.py --bot complaint`
5. `python services/zeabur-gateway/scripts/print-deploy-instructions.py complaint` → 跟步驟做
6. `cp k3s/deployments/wecom-bot-order-transform.yaml k3s/deployments/wecom-bot-complaint.yaml` → 改名稱
7. WeCom 後台填 callback URL

---

## 故障排查

| 症狀 | 排查 |
|---|---|
| WeCom 後台「保存」失敗 | Zeabur gateway logs：`token`/`aes key` 不對；檢查 domain SSL 簽好沒 |
| 地端 agent 連不上 ws | `kubectl logs -f deployment/wecom-bot-order-transform` 看連線錯誤；確認 `wss://order-transform.ikd.ink/ws` 可以 curl 到 |
| 使用者發訊息 bot 不理 | WeCom 應用「可見範圍」沒包含使用者；或群聊未 @ bot |
| bot 回 "我只負責訂單..." | personality.md 的拒絕邏輯，檢查訊息內容是否確實是訂單格式 |
| 多人同時用，session 互串 | 確認 `[pool] max_sessions` 夠；OpenAB 用 WeCom user_id 隔離，理論上不會串 |

---

## 成本

| 項目 | 月費 |
|---|---|
| Zeabur Dev plan | $5（帳號級，可開多個 gateway service） |
| 地端 K3s | $0（用既有機器） |
| 自家 domain | $0（已擁有 ikd.ink） |
| **總計（任何 bot 數量）** | **$5/mo** |

> 若 gateway 數量多到撐爆 Dev plan 額度，再升 Pro $19/mo。

---

## 延伸閱讀

- 模組設計：[services/zeabur-gateway/README.md](../../services/zeabur-gateway/README.md)
- 舊文件（地端 docker compose 模式）：[wecom-setup.md](（已刪除）) — 已淘汰，僅供歷史參考
