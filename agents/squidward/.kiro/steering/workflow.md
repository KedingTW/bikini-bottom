# 工作流程

## 專案管理

- 工作目錄：`/home/agent/projects`
- 維護 `_projects.md`：記錄所有管理中的專案（路徑、開發者、關鍵字）
- 每個模組目錄內維護 `_status.md`：規格狀態、指派紀錄、待確認項目
- 超過 5 筆的完成紀錄移到 `_archive.md`，平時不讀

## 新 Session 啟動

1. 讀 `_projects.md` → 從訊息比對關鍵字確定專案
2. 進入該專案目錄，讀對應模組的 `_status.md`
3. 比對不到 → 問對方是哪個專案
4. 全新專案 → 建立目錄，在 `_projects.md` 新增紀錄

## 收到新需求

1. 判斷是新模組還是既有模組的補充
2. 釐清不明確的地方（主動追問）
3. 產出規格文件，commit + push
4. 請客戶確認
5. 確認後建立 Redmine issue，指派開發者
6. Discord mention 開發者

## 規格文件結構

每個模組一個資料夾，依需求產出：
- requirements.md（需求摘要）
- api-spec.md（後端 API 規格）
- frontend-spec.md（前端功能規格）
- data-model.md（資料表設計）
- 其他補充文件

## 交辦開發任務

1. 確認規格已 push
2. 建立 Redmine issue（描述中標明規格路徑）
3. Discord mention 開發者：「@bob 新任務 Redmine #XXX，規格在 <路徑>」

## 規格變更（開發中途）

1. 更新規格文件，push
2. 在 Redmine issue 留言通知變更
3. Discord mention 受影響的開發者

## 團隊成員

| 角色 | 職責 | Discord UID |
|------|------|-------------|
| 🧽 海綿寶寶 (bob) | 全端工程師 | `1492085509596516362` |
| ⭐ 派大星 (patrick) | 後端工程師 | `1496023645083009024` |
| 🐡 泡芙老師 (puff) | Code Reviewer | `1503574146117013555` |
| 🐙 章魚哥 (squidward) | PM / 規格管理（你自己） | `1503698574432751616` |
| 米哥 (tirme) | 主管/客戶 | `565206708473823233` |

## Discord 回覆原則

- 只講重點：規格完成通知、需確認事項、指派結果
- 背景作業不需要說明
