---
inclusion: manual
---

# 比奇堡開發團隊 — 專案概述

## 這是什麼

這是一個基於 OpenAB 的 Discord AI 開發團隊配置專案。每個角色是一個獨立的 Docker 容器，透過 OpenAB 橋接 Discord 和 kiro-cli，讓 AI agent 在 Discord 上以海綿寶寶卡通角色的身份與使用者互動。

## 架構

- AI 角色使用 OpenAB（Rust）+ kiro-cli，定義在 `agents/` 底下
- 獨立服務（如 slash command bot）定義在 `services/` 底下
- 所有容器透過 `docker-compose.yml` 管理
- 環境變數（token、channel ID、AWS 認證）集中在 `.env`
- 角色的個性和工作規範透過 `.kiro/steering/` 設定

## 目錄結構

```
bikini-bottom/
├── .env                      ← 環境變數（不進 git）
├── .env.example              ← 環境變數範本
├── Dockerfile                ← 基於官方 OpenAB image + git
├── docker-compose.yml        ← 所有服務定義
├── agents/                   ← AI 角色設定
│   ├── bob/                  ← 🧽 海綿寶寶（全端工程師）
│   ├── patrick/              ← ⭐ 派大星（後端工程師）
│   └── gary/                 ← 🐌 小蝸（維運助手，AI 模式未啟用）
├── services/                 ← 獨立服務
│   └── slash-bot/            ← Discord slash command bot（/usage 等）
└── docs/
    └── new-agent-sop.md      ← 新增角色 SOP
```

## 角色清單

| 角色 | 別名 | 職責 | 狀態 |
|------|------|------|------|
| 🧽 海綿寶寶 | bob | 全端工程師 | 運作中 |
| ⭐ 派大星 | patrick | 後端工程師 | 運作中 |
| 🐌 小蝸 | gary | 維運助手 | AI 模式未啟用，slash-bot 使用其 token |

## 常用操作

- 啟動：`docker compose up -d --build`
- 看 logs：`docker compose logs -f bob`
- 更新 OpenAB：`docker compose build --pull && docker compose up -d`
- 新增角色：參考 `docs/new-agent-sop.md`
- 角色登入：`docker exec -it <name> kiro-cli login --use-device-flow`

## 注意事項

- 使用者溝通語言為繁體中文
- `.env` 中的 `AWS_SESSION_TOKEN` 會過期，需定期更新
- 每個角色的 `agents/<name>/` 整個目錄會掛載為容器的 `/home/agent`
- 角色工作產出在 `agents/<name>/projects/`（被 gitignore）
- `memory.md` 是動態記憶，每個環境不同（被 gitignore）

## 角色目錄結構

每個角色的目錄 `agents/<alias>/` 會整個掛載為容器內的 `/home/agent/`。
以下是完整的目錄結構與各目錄用途：

```
agents/<alias>/                     ← 掛載為容器的 /home/agent/
├── config.toml                     ← OpenAB 設定（另掛載為 /etc/openab/config.toml:ro）
├── .kiro/                          ← Kiro User Level 設定（全域，所有專案共用）
│   ├── settings/
│   │   ├── mcp.json                ← MCP server 連線設定
│   │   └── cli.json                ← kiro-cli 設定（自動產生）
│   ├── steering/                   ← 角色的 steering 規則
│   │   ├── personality.md          ← 角色個性、口頭禪、回答風格
│   │   ├── workflow.md             ← 工作流程規範
│   │   └── memory.md              ← 動態記憶（gitignore）
│   ├── skills/                     ← 角色的 skills（未來擴充）
│   └── sessions/                   ← kiro-cli session 資料（自動產生，gitignore）
└── projects/                       ← kiro-cli 的工作目錄（working_dir）
    └── <專案名稱>/                  ← 各專案獨立目錄
        └── .kiro/                  ← Kiro Workspace Level 設定（僅該專案使用）
            ├── settings/
            │   └── mcp.json        ← 專案層級 MCP 設定（覆蓋 User Level）
            ├── steering/           ← 專案層級 steering 規則
            └── skills/             ← 專案層級 skills
```

重要規則：
- User Level（`~/.kiro/`）= 全域設定，所有專案共用
- Workspace Level（`projects/<專案>/.kiro/`）= 專案層級，僅該專案使用，會覆蓋 User Level
- 不要在 `projects/` 根目錄放 `.kiro/`，`projects/` 本身不是 workspace
- `steering/`、`skills/`、`settings/` 在兩個層級都可以存在，各有各的作用範圍
