# Video Digest 處理流程（海綿寶寶專用）

> 更新時間：2026-05-22 14:02 (Asia/Taipei)

---

## 目錄結構

```
/shared/workspace/video-digest/videos/
  index.json                    ← 狀態索引
  {videoId}/
    meta.json                   ← 影片資訊 + 狀態
    transcript.md               ← 逐字稿
    summary.md                  ← 重點摘要
    illustration.png            ← 原始插畫
    illustration_branded.jpg    ← 加框版（推播用）
```

---

## 程序1：處理新影片

| Step | 動作 | MCP Tool |
|------|------|----------|
| 1 | 取得影片資訊 | `GetYoutubeVideoInfo`（youtube-mcp） |
| 2 | 提交 STT 轉錄 | `SttSubmit`（stt-mcp） |
| 3 | Polling 等轉錄完成 | `SttGetResult`（stt-mcp） |
| 4 | 生成摘要 | LLM（不需 tool） |
| 5 | 生成插畫 | `GenerateImage`（image-mcp） |
| 6 | 加品牌框 | `AddBrandFrame`（image-mcp） |
| 7 | 建立 meta.json | 寫檔 |
| 8 | 更新 index.json | processing → pending-review |
| 9 | 通知審核 | mention 米哥 + 珈瑄 |

### 細節

- Step 3：每 30-60 秒 polling 一次，直到 status = completed。超過 10 分鐘回報章魚哥。
- Step 4：3-5 個重點 bullet + 1 個思考題，存為 `summary.md`
- Step 5：存為 `illustration.png`
- Step 6：存為 `illustration_branded.jpg`
- Step 9：mention `<@565206708473823233>` `<@1494150209637318866>`

---

## 程序2：修正（人類說「修正 {videoId}」時）

1. 讀現有檔案
2. 根據反饋重新生成（摘要/插畫）
3. 重新生成插畫 → 也要重跑 `AddBrandFrame`
4. 覆蓋存回
5. 回覆「已修正完成」

---

## 程序3：推播（人類說「推播 {videoId}」時）

| Step | 動作 | MCP Tool |
|------|------|----------|
| 1 | 確保圖片 ≤ 2MB | `ResizeImage`（image-mcp） |
| 2 | 上傳縮圖取 thumbMediaId | `UploadWecomMedia`（wecom-push-mcp） |
| 3 | 上傳內嵌圖片取 url | `UploadWecomImage`（wecom-push-mcp） |
| 4 | 推播 mpnews | `PushWecomMpnews`（wecom-push-mcp） |
| 5 | 歸檔 | 見下方 |

### 細節

- 所有 Wecom tools 傳 `appName: "als"`
- Step 4 的 content 為 HTML 格式（摘要文字 + 內嵌圖片）

### Step 5 歸檔（推到正式機後必須立即執行）

推播成功後，下一步就是歸檔，不可遺漏：

1. 更新 meta.json：`status` → `pushed`，填入 `pushedAt`
2. 更新 meta.json：寫入 `msgIdALS`（正式機推播回傳的 msgId）
3. 移動資料夾：`videos/{videoId}/` → `videos/pushed/{videoId}/`
4. 從 `queues/pending-push.json` 移除該筆
5. 加入 `queues/pushed.json`

### msgId 記錄規則

推播成功時，企微 API 會回傳 msgId，必須寫入 meta.json：

| 推播目標 | 寫入欄位 | 時機 |
|----------|---------|------|
| review 應用（審核） | `msgIdReview` | 推到共讀審核成功時 |
| als 應用（正式機） | `msgIdALS` | 推到正式機成功時 |

用途：後續如需撤回訊息，必須有 msgId 才能操作。

---

## ⚠️ 鐵律

1. STT 必須 polling 等結果，不能拿到 processing 就跳過
2. 遇到任何問題 → 直接回報章魚哥，不要自己找替代方案
3. 所有 Wecom tools 都傳 `appName: "als"`
4. 統一用 `video-digest`，不要出現 `bv-summary`
5. 插畫兩版都保留：`illustration.png` + `illustration_branded.jpg`
6. 加框在審核前就做（程序1 的一部分）
7. **不重複推審核**：推送到 review 應用前，必須先檢查 meta.json 的 status。若已是 `pending-push` 或 `pushed`，代表已通過審核，不可再推去 review，避免造成筱瓔困擾
