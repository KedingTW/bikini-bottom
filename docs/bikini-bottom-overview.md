# 🏝️ 比奇堡開發團隊 — 總覽

> 基於 OpenAB 的 Discord AI 開發團隊，每個角色都是獨立的 AI agent。
> 目前 agents 目錄在 `agents/`（待搬到 `agents/bikini-bottom/`）。

---

## 架構

```
Discord Server: 比奇堡 (Guild: 1492090122257170523)
│
├── AI 角色（OpenAB + kiro-cli）
│   ├── 🧽 海綿寶寶（bob） — 全端工程師
│   ├── ⭐ 派大星（patrick） — 後端工程師
│   ├── 🐋 珍珍（pearl） — 全端工程師
│   ├── 🦞 蝦霸（larry） — 後端工程師
│   ├── 🦑 章魚哥（squidward） — 專案經理 / PM
│   ├── 🐿️ 珊迪（sandy） — 客戶成功經理
│   ├── 🐡 泡芙老師（puff） — Code Review
│   ├── 🐚 神奇海螺（conch） — 團隊神諭者
│   └── 🦸 海超人（mermaid-man） — DevOps
│
├── 獨立服務
│   └── 🐌 小蝸（gary / slash-bot） — 維運助手
│
└── 頻道
    ├── 🍔 蟹堡王 — 工作任務
    ├── 🏖️ 比奇堡廣場 — 閒聊
    ├── 🗿 復活節島會議室 — 商業洽談
    ├── 🧪 珊迪的實驗室 — 技術研究
    ├── 🐛 海蟲回報站 — Bug 回報
    └── 📺 鯡魚電視台 — 公告
```

## 角色說明

| 角色 | 容器名 | 說明 |
|------|--------|------|
| 🧽 海綿寶寶 | `bob` | 全端工程師，主力開發 |
| ⭐ 派大星 | `patrick` | 後端工程師 |
| 🐋 珍珍 | `pearl` | 全端工程師 |
| 🦞 蝦霸 | `larry` | 後端工程師 |
| 🦑 章魚哥 | `squidward` | PM，任務分配與追蹤 |
| 🐿️ 珊迪 | `sandy` | 客戶成功經理 |
| 🐡 泡芙老師 | `puff` | Code Review |
| 🐚 神奇海螺 | `conch` | 團隊神諭者 |
| 🦸 海超人 | `mermaid-man` | DevOps |
| 🐌 小蝸 | `gary` / `slash-bot` | 維運助手 |

## 共用 Skills

| Skill | 用途 |
|-------|------|
| `xlsx` | Excel 產生 |
| `pdf` | PDF 產生 |
| `pptx` | PowerPoint 產生 |
| `docx` | Word 產生 |
| `doc-coauthoring` | 文檔協作 |
| `company-kb` | 科定企業知識庫 |

## 新增角色

參考 [bot-setup-sop-bikini-bottom.md](./bot-setup-sop-bikini-bottom.md)

## 快速指令

```bash
# 看 pod 狀態
kubectl get pods -n bikini-bottom

# 重啟角色
kubectl rollout restart deployment/bob -n bikini-bottom

# 看 log
kubectl logs -f deployment/bob -n bikini-bottom
```
