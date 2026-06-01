# Discord 頻道管理 MCP 工具開發規格

## 概述

為 Discord MCP Server 新增頻道/討論串管理功能，支援批次清除訊息、刪除討論串、管理頻道內容等操作。

## 背景

目前 Discord MCP 僅提供基本的訊息讀寫和 thread 編輯功能，缺乏：
- 批次刪除訊息
- 刪除討論串（thread）
- 批次封存/解封討論串
- 頻道清理（purge）

當 cronjob 或自動化流程產生大量垃圾訊息/thread 時，無法有效清理。

## 需求工具

### 1. DeleteDiscordThread

刪除指定的討論串（使用 `DELETE /channels/{thread_id}` API）。

**參數：**
- `threadId` (required): Thread ID
- `botToken` (optional): Bot Token

**權限需求：** `MANAGE_THREADS`

---

### 2. BulkDeleteMessages

批次刪除頻道或 thread 中的訊息（使用 `POST /channels/{channel_id}/messages/bulk-delete` API）。

**參數：**
- `channelId` (required): 頻道或 Thread ID
- `messageIds` (required): 要刪除的訊息 ID 陣列（最多 100 個）
- `botToken` (optional): Bot Token

**限制：**
- 單次最多 100 則
- 訊息必須在 14 天內
- 需要 `MANAGE_MESSAGES` 權限

---

### 3. PurgeChannelMessages

清除頻道中符合條件的訊息（高階封裝，內部呼叫 BulkDelete）。

**參數：**
- `channelId` (required): 頻道 ID
- `limit` (optional): 最多刪除幾則，預設 100
- `authorId` (optional): 只刪除特定 bot/user 的訊息
- `contains` (optional): 只刪除包含特定關鍵字的訊息
- `before` (optional): 只刪除此訊息 ID 之前的
- `after` (optional): 只刪除此訊息 ID 之後的
- `botToken` (optional): Bot Token

---

### 4. BulkArchiveThreads

批次封存頻道中的討論串。

**參數：**
- `channelId` (required): 父頻道 ID
- `nameContains` (optional): Thread 名稱包含的關鍵字
- `olderThan` (optional): 只處理早於此時間的 thread（ISO 8601）
- `lock` (optional): 是否同時鎖定，預設 true
- `botToken` (optional): Bot Token

---

### 5. BulkDeleteThreads

批次刪除頻道中的討論串。

**參數：**
- `channelId` (required): 父頻道 ID
- `threadIds` (optional): 指定要刪除的 thread ID 陣列
- `nameContains` (optional): Thread 名稱包含的關鍵字（與 threadIds 二擇一）
- `limit` (optional): 最多刪除幾個，預設 100
- `botToken` (optional): Bot Token

**權限需求：** `MANAGE_THREADS`

---

## 實作注意事項

1. **Rate Limiting**: Discord API 有嚴格的 rate limit，需實作：
   - 讀取 `X-RateLimit-Remaining` header
   - 遇到 429 時等待 `Retry-After` 秒數
   - 批次操作間加入適當延遲（建議 200-500ms）

2. **權限檢查**: 操作前應先確認 bot 有足夠權限，否則回傳明確錯誤訊息

3. **安全機制**:
   - BulkDelete/Purge 操作應回傳實際刪除數量
   - 提供 dry-run 模式（只回報會刪除什麼，不實際執行）

4. **回傳格式**:
   ```json
   {
     "success": true,
     "deleted_count": 150,
     "failed_count": 2,
     "details": "Deleted 150 threads, 2 failed due to permissions"
   }
   ```

## 優先順序

1. `BulkDeleteThreads` — 最急需，解決 cron thread 堆積問題
2. `BulkArchiveThreads` — 次要，作為不能刪除時的替代方案
3. `PurgeChannelMessages` — 清理頻道訊息
4. `BulkDeleteMessages` — 底層工具
5. `DeleteDiscordThread` — 單一刪除

## 相關資源

- [Discord API - Delete Channel](https://discord.com/developers/docs/resources/channel#deleteclose-channel)
- [Discord API - Bulk Delete Messages](https://discord.com/developers/docs/resources/channel#bulk-delete-messages)
- 現有 MCP Server: `discord-mcp`
