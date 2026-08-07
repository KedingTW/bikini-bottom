# 語音轉文字（STT）作業流程

> 適用角色：章魚哥、小蝸（PM 收到會議錄影時使用）

## 觸發時機

人類（通常是珈瑄）在 Discord mention 你，告知有新需求並提供會議錄影路徑（在 `/nas/shared/` 下）。

## 操作步驟

### 1. 提交轉錄任務

呼叫 `SttSubmit`，傳入錄影檔的容器內路徑。

```
SttSubmit(filePath: "/nas/shared/drop/xxx.mp4")
```

### 2. 輪詢任務狀態

取得 `taskId` 後，呼叫 `SttGetResult` 查詢狀態。

```
SttGetResult(taskId: 12345)
```

狀態說明：
| 狀態 | 處理方式 |
|------|---------|
| `processing` | 等待 30 秒後重試 |
| `completed` | 取得逐字稿 filePath，進入下一步 |
| `failed` | 回報人類，確認檔案路徑是否正確 |
| `cancelled` | 回報人類，確認是否要重新提交 |

### 3. 讀取逐字稿

從回傳的 `filePath` 讀取 `.txt` 逐字稿內容。

### 4. 整理規格

根據逐字稿內容：
1. 摘要會議重點
2. 識別需求項目
3. 整理成規格文件（依標準規格文件結構）
4. 寫入 `/shared/workspace/{project}/`
5. 請參與會議的人類確認

## 注意事項

- 錄影檔必須在容器可存取的路徑下（通常是 `/nas/shared/`）
- 如果人類給的是 Windows 路徑，依 `shared-drive.md` 規則轉換
- 轉錄時間視檔案長度而定，長影片可能需要數分鐘
- 輪詢間隔建議 30 秒，不要太頻繁
- 轉錄完成後的逐字稿是原始素材，不需要保存到 workspace（規格文件才需要）
