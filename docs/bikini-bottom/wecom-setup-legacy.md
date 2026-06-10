# WeCom Bot 設定指南

透過 OpenAB Gateway 將企業微信（WeCom）連接至 OAB Agent。

## 架構

```
企業微信 ──POST──▶ Gateway (:8080) ◀──WebSocket── wecom-bot (OAB)
                   /webhook/wecom
```

## 前置需求

- Docker & Docker Compose
- 企業微信管理員帳號
- 可被外網 HTTPS 存取的伺服器（用於接收 WeCom 回調）

## 步驟一：建立企業微信應用

1. 登入 [企業微信管理後台](https://work.weixin.qq.com/wework_admin/frame)
2. 進入 **應用管理** → **自建** → **創建應用**
3. 填寫應用名稱、描述，選擇可見範圍
4. 建立後記下：
   - **AgentId** — 應用詳情頁面上方
   - **Secret** — 點擊查看/複製
5. 進入 **我的企業** → 複製 **企業ID (Corp ID)**

## 步驟二：設定 API 接收（回調 URL）

1. 在應用詳情頁，找到 **接收消息** 區塊
2. 點擊 **設置API接收**
3. 填入：
   - **URL**: `https://你的域名/webhook/wecom`（必須 HTTPS）
   - **Token**: 點「隨機獲取」或自訂
   - **EncodingAESKey**: 點「隨機獲取」或自訂
4. **先不要點保存** — 需要先啟動 Gateway 才能驗證 URL

## 步驟三：填寫 .env

將步驟一、二取得的值填入 `.env`：

```env
WECOM_CORP_ID=ww1234567890abcdef      # 企業ID
WECOM_AGENT_ID=1000002                  # 應用AgentId
WECOM_SECRET=your-app-secret            # 應用Secret
WECOM_TOKEN=your-callback-token         # 回調Token
WECOM_ENCODING_AES_KEY=your-43-char-key # 回調EncodingAESKey（43字元）
```

## 步驟四：啟動服務

```bash
# 啟動 Gateway + WeCom Bot
docker compose up -d gateway wecom-bot
```

確認 Gateway 正常運行：
```bash
curl http://localhost:8080/health
```

## 步驟五：驗證回調 URL

1. 回到企業微信管理後台 → 應用 → 接收消息 → 設置API接收
2. 點擊 **保存**
3. 如果 Gateway 正確解密並回應，會看到「保存成功」

### 驗證失敗排查

- 確認 Gateway 可透過 HTTPS 被外網存取
- 確認 `WECOM_TOKEN` 和 `WECOM_ENCODING_AES_KEY` 與管理後台完全一致
- 查看 Gateway logs：`docker compose logs gateway`

## 步驟六：測試

在企業微信中找到你建立的應用，發送一條訊息，Bot 應該會回覆。

## HTTPS 暴露方式

WeCom 要求回調 URL 必須是 HTTPS。常見方案：

### 方案 A：Cloudflare Tunnel（推薦開發用）
```bash
cloudflared tunnel --url http://localhost:8080
```

### 方案 B：Nginx 反向代理 + Let's Encrypt
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /webhook/wecom {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 注意事項

- WeCom 不支援訊息編輯 API，streaming 模式會造成短暫閃爍（預設關閉）
- 群聊需要企業完成實名認證才能使用
- 群聊中 Bot 預設只回應 @mention 的訊息
- 訊息長度限制為 2048 bytes，超長訊息會自動在行邊界分割
