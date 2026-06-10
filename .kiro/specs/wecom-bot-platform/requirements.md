# Requirements Document

## Introduction

WeCom Bot Platform 是一個讓比奇堡團隊把既有的 Discord Agent 知識（最初由 squidward 在 Discord thread 中累積的「訂單資料轉換」規則）抽出來、做成 WeCom（企業微信）專用 bot 的多 bot 平台。每個 bot 只負責單一業務領域（訂單轉換、客訴、HR 等），同事在企業微信私聊即可使用，不需進入 Discord。

部署採混合架構：對外的 WeCom callback gateway 部署在 Zeabur（PaaS、自動 HTTPS），需要連內網 MCP 的 bot 留在地端 K3s；地端 bot 主動以 outbound WebSocket 連到 Zeabur gateway，公司防火牆零 inbound 變動。

第一個交付的 bot 是 `wecom-bot-order-transform`（訂單資料轉換）。第二個 bot 起，必須能複製第一個 bot 的模式快速上線。

## Glossary

- **Platform**: 整個 WeCom 多 bot 平台，包含 Zeabur gateway、地端 K3s bot、設定流程、文件等
- **Bot_Service**: 一個對應單一業務的 WeCom bot（如 `wecom-bot-order-transform`），由「1 個 WeCom 應用 + 1 個 Zeabur gateway service + 1 個地端 K3s deployment」三件套組成
- **Zeabur_Gateway**: 部署在 Zeabur 的 OpenAB Gateway 實例，負責接收 WeCom callback、解密訊息、與地端 bot 之間維持 WebSocket 通道
- **Local_Bot**: 部署在地端 K3s 的 OpenAB agent 容器，主動以 wss outbound 連線 Zeabur_Gateway，並可存取內網 MCP server
- **WeCom_Application**: 在企業微信後台建立的自建應用，每個 Bot_Service 對應一個 WeCom 應用，有獨立的 AgentId 和 Secret
- **WeCom_Callback_URL**: WeCom 應用後台設定的「接收消息」回調 URL，格式為 `https://wecom-{業務}.ikd.ink/webhook/wecom`
- **MCP_Server**: 內網的 Model Context Protocol 服務（sap、crm、als、hrs、pricing 等），位址為 `http://192.168.1.105:1601/mcp/*` 或 `http://host.docker.internal:1601/mcp/*`
- **Order_Bot**: 第一個 Bot_Service，agent 名稱 `wecom-bot-order-transform`，唯一職責為訂單資料轉換
- **Order_Transform_Rules**: 章魚哥（squidward）累積的訂單資料轉換規則文件，路徑 `agents/squidward/order-data-transform-rules.md`
- **Bot_Template**: 從 Order_Bot 抽取出來的、可複製給後續 Bot_Service 使用的目錄結構與設定範本
- **OpenAB_Pool**: OpenAB agent 內建的 session pool，會為每個 WeCom user_id 自動開獨立的 kiro-cli session
- **ICP_Domain**: 公司已備案的網域 `ikd.ink`
- **WeCom_Secrets**: 5 個 WeCom 應用密鑰（CORP_ID、AGENT_ID、SECRET、TOKEN、ENCODING_AES_KEY），由 WeCom 後台產生
- **Legacy_Local_Gateway**: 既有部署在地端的 OpenAB gateway（`k3s/deployments/gateway.yaml`、`docker-compose.yml` 的 gateway service），本平台啟用後將被廢除

## Requirements

### Requirement 1: 混合部署架構

**User Story:** As a 平台維運者, I want WeCom callback gateway 部署在 Zeabur 而 bot 留在地端 K3s, so that 公司防火牆不需要開放任何 inbound 連線即可讓企業微信送訊息進來

#### Acceptance Criteria

1. THE Platform SHALL 將每個 Bot_Service 的 Zeabur_Gateway 部署在 Zeabur PaaS 環境
2. THE Platform SHALL 將每個 Bot_Service 的 Local_Bot 部署在地端 K3s cluster 的 `bikini-bottom` namespace
3. THE Local_Bot SHALL 主動以 outbound WebSocket（wss）連線到 Zeabur_Gateway，連線方向為「地端 → 雲端」
4. THE Platform SHALL NOT 要求公司防火牆新增任何 inbound 規則
5. WHEN 一個 Bot_Service 啟用時, THE Platform SHALL 提供唯一一組 ICP_Domain 子網域（格式 `wecom-{業務}.ikd.ink`）作為該 bot 的 WeCom_Callback_URL host
6. THE Zeabur_Gateway SHALL 由 Zeabur 自動提供 HTTPS 憑證
7. WHERE Local_Bot 需要查詢內部資料, THE Local_Bot SHALL 透過內網位址連線 MCP_Server，不經過 Zeabur_Gateway

### Requirement 2: 一對一的 Bot_Service 編組

**User Story:** As a 平台維運者, I want 每個業務領域對應一個獨立的 WeCom 應用、Zeabur gateway 與地端 bot, so that bot 之間互相隔離、密鑰不互通、可以分別啟停

#### Acceptance Criteria

1. THE Platform SHALL 對每個 Bot_Service 建立 1 個 WeCom_Application、1 個 Zeabur_Gateway service、1 個 Local_Bot deployment
2. WHERE 同一個業務有多位同事使用, THE OpenAB_Pool SHALL 為每個 WeCom user_id 開立獨立的 kiro-cli session
3. THE Platform SHALL 確保不同 Bot_Service 之間不共用 KIRO_API_KEY、WeCom_Secrets、git identity
4. THE Platform SHALL 確保新增、停用或重啟一個 Bot_Service 不影響其他 Bot_Service 的運作
5. WHEN 一個 Bot_Service 對應的 Zeabur_Gateway 重啟時, THE Local_Bot SHALL 自動重連並恢復服務

### Requirement 3: 第一個 Bot — Order_Bot 的職責邊界

**User Story:** As a 訂單轉換 bot 使用者, I want bot 只回答訂單資料轉換相關問題, so that 對話內容專注、不會被其他話題干擾

#### Acceptance Criteria

1. THE Order_Bot SHALL 將 agent 名稱命名為 `wecom-bot-order-transform`
2. THE Order_Bot SHALL 把唯一職責限定為「訂單資料轉換」
3. WHEN 使用者送出非訂單資料轉換的訊息, THE Order_Bot SHALL 回覆固定訊息「我只負責訂單資料轉換」並停止繼續回應該訊息
4. WHEN 使用者送出訂單資料轉換訊息, THE Order_Bot SHALL 依 Order_Transform_Rules 輸出品號、數量（必要時含對花備註）三個區塊
5. THE Order_Bot SHALL 在 personality steering 中明文寫出「我只負責訂單資料轉換，其他問題一律拒絕」作為強制邊界
6. WHEN 使用者第一次發訊息（如「你好」、空訊息或非業務問候）, THE Order_Bot SHALL 回覆「我只負責訂單資料轉換，請直接貼客戶的訂購訊息」
7. THE Order_Bot SHALL 直接輸出可複製到 Ragic 平台的品號、數量、對花備註，不附加多餘解釋

### Requirement 4: 從 squidward 繼承知識（不繼承人格）

**User Story:** As a Order_Bot 開發者, I want bot 沿用 squidward 累積的訂單規則但不沿用章魚哥的個性, so that 同事看到的是專業的業務助理而非帶情緒的章魚哥

#### Acceptance Criteria

1. THE Order_Bot SHALL 把 `agents/squidward/order-data-transform-rules.md` 的內容複製為自己的 steering 檔案
2. THE Order_Bot SHALL 在 OpenAB 啟動時自動載入該規則檔（auto-loaded steering）
3. THE Order_Bot SHALL NOT 繼承 squidward 的 `personality.md`、口頭禪、或對特定人物（如筱瓔、海綿寶寶）的特殊互動邏輯
4. THE Order_Bot SHALL 使用獨立的 personality steering，內容只描述「訂單資料轉換助理」的角色與邊界
5. WHEN squidward 的 `order-data-transform-rules.md` 後續更新, THE Platform SHALL 提供明確的同步機制（手動或腳本），由維運者主動觸發更新到 Order_Bot
6. THE Order_Bot SHALL 只保留 `kd-product-coding` 一個 skill；squidward 既有的其他 skill（kd-complaint-handler、kd-crm-operations、kd-pricing-assistant、kd-meeting-updates、kd-glossary、kd-company-knowledge、kd-product-knowledge、xlsx、pdf、pptx、docx、doc-coauthoring、company-kb 等）SHALL NOT 被載入
7. THE Order_Bot SHALL 只連線 `sap-mcp` 一個 MCP server（用於呼叫 ValidateProductCode 工具）
8. THE Order_Bot SHALL NOT 連線 `crm-mcp`、`als-mcp`、`hrs-mcp`、`pricing-mcp`、`wecom-drive-mcp`、`youtube-mcp`、`stt-mcp`、`wecom-push-mcp`、`image-mcp`、`file-mcp`、`ragic-mcp`

### Requirement 5: 安全與密鑰管理

**User Story:** As a 平台維運者, I want WeCom 應用密鑰、KIRO API Key 等敏感資料不進 git, so that 倉庫公開或洩漏不會直接暴露生產環境密鑰

#### Acceptance Criteria

1. THE Platform SHALL NOT 將 WeCom_Secrets（CORP_ID、AGENT_ID、SECRET、TOKEN、ENCODING_AES_KEY）的實際值寫入任何 git-tracked 檔案
2. THE Platform SHALL NOT 將 KIRO_API_KEY 的實際值寫入任何 git-tracked 檔案
3. WHEN 首次部署一個 Bot_Service 到 Zeabur, THE 維運者 SHALL 在 Zeabur Dashboard 手動填入該 Bot_Service 的 5 個 WeCom_Secrets
4. THE 地端 Local_Bot SHALL 透過 K3s Secret 物件取得 KIRO_API_KEY，Secret 內容由維運者手動建立、不進 git
5. WHERE Bot_Service 啟用 Zeabur API 自動化, THE Platform SHALL 使用 `.env` 中的 `ZEABUR_KEY` 進行 API 操作，且 `.env` SHALL 在 `.gitignore` 中
6. THE Platform SHALL 在 `.env.example` 中列出每個 Bot_Service 所需的環境變數名稱（不含實際值）作為文件
7. IF 任何 commit 嘗試寫入符合密鑰格式的字串到 git-tracked 檔案, THEN THE 維運者 SHALL 在 commit 前手動移除（本要求由人工 review 把關，無自動 hook）

### Requirement 6: 廢除 Legacy_Local_Gateway

**User Story:** As a 平台維運者, I want 舊的地端 gateway 部署被完整移除, so that WeCom callback 只有 Zeabur 一條路徑、不會兩邊收一份造成行為混亂

#### Acceptance Criteria

1. THE Platform SHALL 從 `k3s/kustomization.yaml` 的 `resources` 列表移除 `deployments/gateway.yaml` 條目
2. THE Platform SHALL 刪除 `k3s/deployments/gateway.yaml` 檔案
3. THE Platform SHALL 從 `docker-compose.yml` 移除 `gateway` service 區塊
4. THE Platform SHALL 從 `docker-compose.yml` 移除 `wecom-bot` service 對 `gateway` 的 `depends_on` 依賴
5. THE Platform SHALL NOT 保留地端 gateway 作為 Zeabur 的 failover，理由是 WeCom_Callback_URL 只能設定一個值，無 failover 意義
6. WHEN Legacy_Local_Gateway 移除完成後, THE 既有 `agents/wecom-bot/` 目錄 SHALL 被改名為 `agents/wecom-bot-order-transform/`
7. THE 改名後的 `agents/wecom-bot-order-transform/config.toml` SHALL 重新指向 Zeabur_Gateway 的 wss URL，不再指向地端 `ws://gateway:8080/ws`

### Requirement 7: 多 Bot 擴展模式

**User Story:** As a 平台維運者, I want 第一個 bot 上線後可複製其結構快速新增第二個 bot, so that 後續每加一個業務 bot（如客訴、HR）的設定流程一致且可預期

#### Acceptance Criteria

1. THE Platform SHALL 從 Order_Bot 抽取出 Bot_Template，包含 agent 目錄結構、K3s deployment 範本、Zeabur gateway service 範本
2. THE Bot_Template SHALL 以文件形式（如 `docs/wecom-bot-new-bot-sop.md`）說明新增一個 Bot_Service 必須執行的步驟
3. THE 新增 Bot_Service 的 SOP SHALL 至少涵蓋以下五個步驟：
   a. 複製 agent 目錄、修改 personality + steering + skills + MCP 設定
   b. 複製 K3s deployment YAML、修改 deployment 名稱與 secret 引用
   c. 複製 Zeabur gateway service 設定，並填入新的 5 個 WeCom_Secrets
   d. 在 WeCom 後台建立新自建應用、設定 WeCom_Callback_URL
   e. 在 DNS 服務商為 `wecom-{業務}.ikd.ink` 加 CNAME 記錄指向 Zeabur 提供的 domain
4. WHEN 新增 Bot_Service 完成步驟 a~e, THE 新 Bot_Service SHALL 能獨立運作，不影響既有 Bot_Service
5. THE Bot_Template SHALL 不包含任何 Order_Bot 特定的業務規則或密鑰
6. THE Platform SHALL 在 `.env.example` 中為新 Bot_Service 預留變數命名規範（例：`KIRO_API_KEY_WECOM_BOT_{業務}`）

### Requirement 8: 同事使用體驗驗收

**User Story:** As a 沒有 Discord 帳號的同事, I want 在企業微信私聊 Order_Bot 直接得到訂單轉換結果, so that 不需安裝任何工具就能用到既有的訂單轉換能力

#### Acceptance Criteria

1. WHEN 同事在企業微信私聊 Order_Bot 發送「你好」, THE Order_Bot SHALL 回覆「我只負責訂單資料轉換，請直接貼客戶的訂購訊息」
2. WHEN 同事在企業微信私聊 Order_Bot 發送「今天天氣」或其他非業務話題, THE Order_Bot SHALL 回覆「我只負責訂單資料轉換」
3. WHEN 同事發送類似「P181G. 2x8皮=2。 3mm. =7」的訂單訊息, THE Order_Bot SHALL 回覆三個區塊：品號區塊、數量區塊、對花備註區塊（無裁切時對花備註區塊可省略或留白）
4. WHEN 多位同事同時透過 Order_Bot 提問, THE OpenAB_Pool SHALL 為每位同事的 WeCom user_id 維持獨立的對話 session，互不串味
5. WHEN 同事在訊息中包含色號（如 `181G`）, THE Order_Bot SHALL 透過 sap-mcp 的 ValidateProductCode 工具驗證色號是否存在後再輸出結果
6. THE Order_Bot SHALL 在 `wecom-bot-order-transform` 的可見範圍內（即 WeCom 後台應用設定的成員）對所有同事可用，初版以訂單業務 10 位同事為範圍
7. WHEN Order_Bot 收到訂單訊息且 ValidateProductCode 顯示色號不存在, THE Order_Bot SHALL 在輸出中以 `?` 標示該品項並備註「色號不存在」，不可猜測

### Requirement 9: Zeabur 部署與自動化

**User Story:** As a 平台維運者, I want 使用 Zeabur API 在後續可以自動化建立/更新 gateway service, so that 新增 Bot_Service 時可減少手動點擊操作

#### Acceptance Criteria

1. THE Platform SHALL 將 `ZEABUR_KEY` 環境變數記載在 `.env.example` 中（不含實際值）
2. WHERE 維運者選擇使用 Zeabur API 自動化, THE Platform SHALL 提供腳本或文件說明如何用 `ZEABUR_KEY` 建立新的 service
3. WHEN 首次建立一個 Bot_Service 對應的 Zeabur service, THE 維運者 SHALL 在 Zeabur Dashboard 手動填入 5 個 WeCom_Secrets，理由是避免密鑰寫入 git 或腳本參數
4. WHEN WeCom 後台需要點擊「保存」驗證 WeCom_Callback_URL, THE 該操作 SHALL 由具備 WeCom 管理員權限的真人完成，不在自動化範圍內
5. WHERE 維運者使用 Zeabur Dev plan, THE Platform SHALL 確認多個 Bot_Service 的 Zeabur_Gateway service 共用同一個帳號級 $5/月額度

### Requirement 10: 不在範圍內（明確排除）

**User Story:** As a 維運者, I want 明確列出本次不做的項目, so that 開發過程不被擴張範圍

#### Acceptance Criteria

1. THE Platform SHALL NOT 使用 WeCom JS-SDK、可信域名、可信 IP 等網頁端整合機制
2. THE Platform SHALL NOT 使用 AWS Lambda、Fargate、Lightsail 作為 gateway 部署目標
3. THE Platform SHALL NOT 使用 Cloudflare Tunnel 作為 HTTPS 暴露機制
4. THE Platform SHALL NOT 重新實作或修改 Order_Transform_Rules 的內部邏輯，僅原樣引用既有規則
5. THE Platform SHALL NOT 在本次交付中實作客訴、HR 等其他 Bot_Service 的細節，僅要求架構可擴展
