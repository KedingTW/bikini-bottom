# Zeabur Gateway 模組

> 模組化管理「WeCom 應用 → Zeabur OpenAB Gateway → 地端 K3s wecom-bot agent」的部署設定。
> 為了讓未來 admin web UI 能直接重用 `lib/`，所有設定以 YAML 為單一事實來源。

---

## 架構

```
WeCom 應用 (1 對 1)        ──HTTPS──▶ Zeabur gateway-<name>  (1 對 1)  ◀══wss══ 地端 K3s wecom-bot-<name>  ──▶ 內網 MCP
   - 每個業務一個 WeCom 應用            - image: openab-gateway              - kiro-cli + skill + steering
   - 5 個密鑰                            - 純 stateless webhook              - session pool（每個同事獨立）
```

## 目錄結構

```
services/zeabur-gateway/
├── README.md                     # 本檔
├── bots/                         # 每個 bot 一份 YAML（單一事實來源）
│   ├── _template.yaml            # 範本
│   └── order.yaml                # 第一個：訂單轉換
├── lib/                          # Python 模組（admin 也會 import）
│   ├── __init__.py
│   ├── bot_config.py             # BotConfig / BotRegistry
│   └── zeabur_client.py          # Zeabur GraphQL API client
├── schema/
│   └── bot.schema.json           # JSON schema（IDE 補全用）
└── scripts/                      # CLI 工具
    ├── list-bots.py              # 列出所有 bot
    ├── check-env.py              # 檢查 .env 密鑰齊全
    └── print-deploy-instructions.py  # 印出 Zeabur 部署步驟
```

## 新增一個 wecom bot 的完整流程

例：要加 `complaint`（客訴 bot）。

### 1. 建 bot 設定

```bash
cp services/zeabur-gateway/bots/_template.yaml services/zeabur-gateway/bots/complaint.yaml
# 編輯 complaint.yaml：填 name=complaint、domain=complaint.ikd.ink、agent=wecom-bot-complaint、envVarPrefix=COMPLAINT、enabled=true
```

### 2. 建地端 wecom-bot agent

```bash
cp -r agents/wecom-bot-order-transform/ agents/wecom-bot-complaint/
# 編輯：
#   agents/wecom-bot-complaint/.kiro/steering/personality.md  改業務範圍
#   agents/wecom-bot-complaint/.kiro/steering/order-rules.md  換成客訴規則
#   agents/wecom-bot-complaint/.kiro/settings/mcp.json        換需要的 MCP
#   agents/wecom-bot-complaint/config.toml                    改 gateway.url = wss://complaint.ikd.ink/ws
```

### 3. 加 .env 密鑰

```env
# .env
COMPLAINT_WECOM_CORP_ID=...
COMPLAINT_WECOM_AGENT_ID=...
COMPLAINT_WECOM_SECRET=...
COMPLAINT_WECOM_TOKEN=...
COMPLAINT_WECOM_ENCODING_AES_KEY=...
KIRO_API_KEY_WECOM_BOT_COMPLAINT=...
```

### 4. 檢查設定齊全

```bash
python services/zeabur-gateway/scripts/check-env.py --bot complaint
```

### 5. 印出 Zeabur 部署步驟並執行

```bash
python services/zeabur-gateway/scripts/print-deploy-instructions.py complaint
# 跟著步驟在 Zeabur dashboard 操作（或之後等 zeabur_client.py 補完後改自動）
```

### 6. 加 K3s deployment

```bash
cp k3s/deployments/wecom-bot-order-transform.yaml k3s/deployments/wecom-bot-complaint.yaml
# 編輯：name 改 wecom-bot-complaint、KIRO_API_KEY 對應的 secret key 改 WECOM_BOT_COMPLAINT
# 改 kustomization.yaml 加入新檔案
kubectl apply -k k3s/
```

### 7. WeCom 後台

到 WeCom 管理後台填回調 URL，確認驗證通過。

---

## 為何模組化、為何 YAML

1. **單一事實來源**：bot 列表、domain、密鑰映射全在 `bots/*.yaml`，避免散落多處
2. **未來 admin UI**：`lib/bot_config.py` 已寫成可直接 import 的 dataclass，admin web 載入後就有完整資料
3. **新增成本固定**：照流程 7 步，每步可獨立驗證
4. **避免人為遺漏**：`check-env.py` 自動檢查密鑰齊全；`print-deploy-instructions.py` 防止漏設變數

---

## 未來進 admin 的設計

`lib/` 下的物件已預留 admin 整合：

```python
# 未來 admin backend 會這樣用：
from services.zeabur_gateway.lib import BotRegistry, ZeaburClient

# 列出所有 bot（給前端表格用）
registry = BotRegistry.load("services/zeabur-gateway/bots")
return [b for b in registry.bots]

# 新增 bot（admin 寫入 YAML + 觸發 Zeabur 部署）
client = ZeaburClient(api_key=os.environ["ZEABUR_API_KEY"])
client.create_service_from_image(name=bot.zeabur_service_name, image=GATEWAY_IMAGE)
```

當 `ZeaburClient` 的 mutation 補齊後，admin 就能：
- 一鍵新增/刪除 bot（同步 YAML + Zeabur + K3s）
- 同步檢查 Zeabur 上實際部署 vs YAML 期望
- 修改密鑰、輪替（更新 .env + redeploy）
