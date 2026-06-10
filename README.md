# 🏝️ 比奇堡 + 科定 AI 服務

基於 [OpenAB](https://github.com/openabdev/openab) 的多組 AI Bot 平台，共用 K3s 基礎設施。

---

## 組別

| 組 | 平台 | 用途 | 使用者 | 目錄 | 狀態 |
|---|---|---|---|---|---|
| 比奇堡團隊 | Discord | AI 開發團隊（通用 agent） | 開發者 | `agents/`（待搬到 `agents/bikini-bottom/`） | ✅ |
| 科定AI服務 | Discord | 業務專用 bot（單一職責） | 同事 | `agents/keding-dc/` | ✅ |
| 科定WeCom | WeCom | 企業微信 bot | 同事 | `agents/keding-wecom/` | ⏸ 暫停 |

---

## 快速連結

### 文件

| 文件 | 用途 |
|------|------|
| [新增 Bot SOP（索引）](docs/bot-setup-sop.md) | 決定加哪組、照哪份 SOP |
| [比奇堡總覽](docs/bikini-bottom-overview.md) | 比奇堡架構、角色、頻道 |
| [科定DC 設定](docs/keding-dc-setup.md) | 伺服器 / 頻道 / Bot 配置 |
| [科定WeCom 部署](docs/wecom-zeabur-setup.md) | Zeabur gateway 部署（暫停） |
| [.env 遷移 SOP](docs/env-rename-migration-sop.md) | 環境變數改名流程 |
| [K3s 遷移規劃](docs/k3s-migration-plan.md) | Docker Compose → K3s |
| [CHANGELOG](CHANGELOG.md) | 變更紀錄 |

### 管理工具

| 工具 | 位置 | 用途 |
|------|------|------|
| Admin Dashboard | `services/admin/` | Web 管理介面（角色狀態、MCP、成本） |
| Zeabur Gateway 模組 | `services/zeabur-gateway/` | WeCom gateway 部署管理 |
| Slash Bot | `services/slash-bot/` | Discord 維運指令（/status, /usage） |

---

## 基礎設施

| 元件 | 說明 |
|------|------|
| K3s | 單節點 Ubuntu Desktop，跑所有 bot |
| NAS | 192.168.1.218（比奇堡 projects 用，`88.BikiniBottom`） |
| MCP Server | 192.168.1.105:1601（pricing / crm / als / hrs / sap 等） |
| Zeabur | WeCom gateway 雲端代理（暫停中） |
| Image | `bikini-bottom/agent:latest`（共用，基於 OpenAB 0.8.4） |

---

## 目錄結構

```
bikini-bottom/
├── agents/
│   ├── bob/, patrick/, ...      ← 比奇堡團隊（待搬到 agents/bikini-bottom/）
│   ├── keding-dc/               ← 科定AI服務 (DC)
│   │   └── order-transform/     ← 下單小幫手
│   └── keding-wecom/            ← 科定WeCom（暫停）
│       └── order-transform/
├── k3s/                         ← K3s deployment YAML
├── services/
│   ├── admin/                   ← 管理後台
│   ├── slash-bot/               ← Discord 維運指令
│   └── zeabur-gateway/          ← WeCom gateway 模組
├── shared/                      ← 比奇堡共用 steering / skills
├── scripts/                     ← entrypoint、部署腳本
├── docs/                        ← 所有文件
├── Dockerfile                   ← Agent image
├── docker-compose.yml           ← Docker Compose（保留，K3s 為主）
├── .env / .env.example          ← 環境變數
└── TODO.md                      ← 待辦事項
```

---

## 授權

MIT
