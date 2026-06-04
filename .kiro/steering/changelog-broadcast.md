---
inclusion: fileMatch
fileMatchPattern: "CHANGELOG.md"
---

# Changelog 廣播規則

## 觸發時機

當 `CHANGELOG.md` 被修改並儲存後，主動詢問使用者是否要將更新內容推送到 Discord 電視台頻道。

## 推送流程

1. 識別本次新增的 changelog 條目（通常是最上方新增的日期區塊）
2. 擬好公告稿，**先呈現給使用者審核**
3. 使用者確認 OK 後，才使用 Discord MCP 工具發送訊息到電視台頻道
4. **未經使用者確認不得發送**

## 訊息格式

推送到 Discord 時，使用以下格式：

```
📋 **比奇堡海灘更新公告** — {日期}

{逐條列出變更，使用 emoji 區分類型}
```

### 類型 Emoji 對照

| 類型 | Emoji |
|------|-------|
| feat | ✨ |
| fix | 🐛 |
| docs | 📝 |
| chore | 🔧 |
| refactor | ♻️ |
| misc | 📦 |

### 範例

```
📋 **比奇堡海灘更新公告** — 2026-06-01

✨ 新增 Karen — Discord token holder，用於 MCP Server 管理
🐛 PR title 規則統一用自己的角色名稱，不再用交辦人名稱
```

## 注意事項

- 只推送「本次新增」的條目，不要重複推送舊的
- 如果使用者選擇不推送，尊重決定不再追問
- 電視台頻道 ID：`1503704168257556551`（CHANNEL_TV）
- 使用 `mcp_discord_mcp_SendDiscordMessage` 工具，channelId 填入上述值
