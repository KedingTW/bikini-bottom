# 神奇海螺升級 — 需求

## 背景

神奇海螺目前是純腳本型 Discord bot（`services/magic-conch/`），只提供 slash command 做容器管理。要將它升級為完整的 OpenAB AI agent，讓團隊成員在無助時可以 mention 它求助。

## 目標

1. 將海螺的 slash command（容器管理）搬給小蝸（`services/slash-bot/`）
2. 退役 `services/magic-conch/` 容器
3. 新建 `agents/conch/` OpenAB agent，使用現有的 `DISCORD_BOT_TOKEN_CONCH`
4. 神奇海螺成為團隊的「神諭者」— 被 mention 時以簡短、神秘的風格回答

## 功能需求

### 小蝸接收的指令（從海螺搬過來）

| 指令 | 功能 | 權限 |
|------|------|------|
| `/status [target]` | 查看容器狀態 | 所有人 |
| `/heal [target]` | 重啟容器 | 操作員 |
| `/logs [target] [lines]` | 查看容器 log | 所有人 |
| `/archive [reason]` | 封存 thread，開新 thread 延續 | 操作員 |

- 指令前綴從 `/conch-*` 改為不帶前綴（或用 `/gary-*`，待確認）
- 小蝸需要新增 docker SDK 和 OpenAI 依賴
- 小蝸的容器需要掛載 docker.sock

### 神奇海螺 OpenAB Agent

- **頻道**：蟹堡王論壇、會議室論壇、廣場、實驗室、電視台、急診室
- **觸發**：被 mention 時回答
- **個性**：簡短、神秘、果斷，偶爾拒絕回答
- **能力**：
  - 團隊求助（卡住時給方向）
  - 流程導航（該找誰、該怎麼做）
  - 跨角色知識（看得到所有頻道）
- **不做**：不寫程式碼、不開 PR、不管專案、不管容器

## 非功能需求

- 海螺的 OpenAB agent 用現有的 `DISCORD_BOT_TOKEN_CONCH` 和 `KIRO_API_KEY_CONCH`
- 小蝸用現有的 `DISCORD_BOT_TOKEN_GARY`
- 不需要新建 Discord Application
