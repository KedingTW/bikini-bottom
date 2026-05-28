# 需求文件：自動日報撰寫機制

## 簡介

本功能為比奇堡 AI Agent 團隊建立自動化日報撰寫機制。每位需要寫日報的 AI 角色於每日晚間 10 點自動回顧當日工作活動，並產出結構化日報檔案。日報作為團隊的長期記憶歸檔、自我改善迴路、跨角色協作感知的核心機制。

資料來源為各專案 `_status.md` 的「最近完成」區段（當日日期項目）與 git log（當日 commit 記錄），不依賴 session 記憶。

## 詞彙表

- **Agent**：運行於 Docker 容器中的 AI 角色，使用 OpenAB 框架與 kiro-cli 執行任務
- **Daily_Report**：每日自動產出的 Markdown 格式工作報告檔案，作為長期記憶歸檔
- **Cronjob_Scheduler**：OpenAB 框架內建的排程機制，透過 `cronjob.toml` 設定 cron 表達式觸發任務
- **Status_File**：各專案的 `_status.md` 檔案，記錄當前任務、最近完成項目與待確認事項
- **Project_Registry**：各角色的 `projects/_projects.md` 檔案，列出該角色負責的所有專案
- **Report_Directory**：日報存放的共享目錄，路徑為 `/shared/reports/daily/{角色名}/`
- **Report_Writer**：負責彙整活動資料並產出日報的處理邏輯
- **Work_Segment**：工作段落，定義為一個可交付成果（結果導向），如 PR 提交、功能完成、文件產出、POC 結論、Review 結論、部署上線
- **Self_Reflection**：日報中的「今日自我檢討」區段，記錄當日工作反思與改善方向

## 需求

### 需求 1：日報排程觸發

**使用者故事：** 身為團隊管理者，我希望每位 AI 角色每天自動撰寫日報，以便追蹤團隊每日工作進度。

#### 驗收條件

1. WHEN 系統時間到達每日 22:00（Asia/Taipei 時區），THE Cronjob_Scheduler SHALL 觸發該 Agent 的日報撰寫流程
2. THE Cronjob_Scheduler SHALL 透過各 Agent 的 `cronjob.toml` 設定排程，使用 cron 表達式 `0 22 * * *`
3. THE Cronjob_Scheduler SHALL 僅對以下角色觸發日報撰寫：bob、patrick、puff、squidward、sandy
4. THE Cronjob_Scheduler SHALL 排除 gary（小蝸）的日報撰寫，因其為獨立 slash-bot 服務而非 AI Agent
5. THE Cronjob_Scheduler SHALL 排除 wecom-bot 的日報撰寫，因其為訊息轉發服務而非需要自我回顧的角色

### 需求 2：活動資料收集

**使用者故事：** 身為 AI 角色，我需要回顧今天做了哪些事情，以便撰寫準確的日報內容。

#### 驗收條件

1. WHEN 日報撰寫流程啟動，THE Report_Writer SHALL 讀取該 Agent 的 Project_Registry 取得所有負責專案清單
2. WHEN 日報撰寫流程啟動，THE Report_Writer SHALL 讀取各專案的 Status_File 中「最近完成」區段，篩選出當日日期的項目
3. WHEN 日報撰寫流程啟動，THE Report_Writer SHALL 執行 `git log --since="today 00:00" --until="today 23:59" --oneline` 取得各專案當日的 commit 記錄
4. THE Report_Writer SHALL 以 Status_File 為主要資料來源，git log 為補充資料來源（補捉 Status_File 未記錄的零散 commit）
5. IF 某專案的 Status_File 與 git log 均無當日紀錄，THEN THE Report_Writer SHALL 不將該專案列入日報
6. IF 所有資料來源均無當日活動紀錄，THEN THE Report_Writer SHALL 產出一份標註「今日無工作紀錄」的日報

### 需求 3：_status.md 紀錄規範

**使用者故事：** 身為 AI 角色，我需要明確的紀錄規範，以便在工作告一段落時正確更新 _status.md，確保日報有充足的資料來源。

#### 驗收條件

1. WHEN Agent 完成一個 Work_Segment，THE Agent SHALL 立即更新該專案的 Status_File「最近完成」區段
2. THE Agent SHALL 以可交付成果（結果導向）作為紀錄單位，每個 Work_Segment 記錄為一筆
3. THE Status_File SHALL 將以下類型視為獨立的 Work_Segment：PR 提交、功能完成、文件產出、POC 結論、Review 結論、部署上線
4. THE Status_File SHALL 將以下類型合併為同一筆 Work_Segment 而非分開記錄：同一 PR 的反覆修改、debug 過程、文件小修、同一 PR 多輪 review
5. THE Status_File 的「最近完成」區段 SHALL 使用格式 `[YYYY-MM-DD HH:mm]` 或 `[YYYY-MM-DD]` 作為每筆紀錄的時間標記
6. WHEN 日報撰寫完成後，THE Report_Writer SHALL 清除 Status_File「最近完成」區段中超過 3 天的紀錄
7. THE Report_Writer SHALL 保留 3 天內（含當日）的紀錄於 Status_File 中，以供跨日參考

### 需求 4：日報檔案產出

**使用者故事：** 身為團隊管理者，我希望日報以統一格式存放在固定位置，以便查閱和歸檔。

#### 驗收條件

1. THE Report_Writer SHALL 將日報檔案寫入路徑 `/shared/reports/daily/{角色名}/YYYY-MM-DD.md`
2. THE Report_Writer SHALL 使用以下 Markdown 格式撰寫日報：
   ```
   # {角色名} 日報 - YYYY-MM-DD

   ## {專案名稱A}
   - {完成項目1}
   - {完成項目2}

   ## {專案名稱B}
   - {完成項目3}

   ## 今日自我檢討
   {一段自由發揮的反思文字}
   ```
3. IF 日報檔案路徑中的目錄不存在，THEN THE Report_Writer SHALL 自動建立所需目錄
4. IF 同日期的日報檔案已存在，THEN THE Report_Writer SHALL 覆寫該檔案（以最新產出為準）

### 需求 5：今日自我檢討格式

**使用者故事：** 身為團隊管理者，我希望每位角色在日報中進行自我反思，以便建立自我改善迴路，未來可從中提取 pattern 調整 steering。

#### 驗收條件

1. THE Report_Writer SHALL 在日報末尾產出「今日自我檢討」區段，以自由發揮的一段文字撰寫
2. THE Self_Reflection SHALL 涵蓋以下引導方向（不強制每項都寫，視當日情況自然帶入）：今天什麼做得順利、什麼卡住了或花太多時間、被人類或其他角色糾正的事、明天應該優先處理什麼
3. IF 當日無任何工作紀錄，THEN THE Report_Writer SHALL 在自我檢討中說明可能原因（如無任務指派、等待中、系統問題）

### 需求 6：日報存放與共享

**使用者故事：** 身為團隊成員，我希望能查閱其他角色的日報，以便了解團隊整體工作狀況並作為長期記憶歸檔。

#### 驗收條件

1. THE Report_Directory SHALL 位於共享掛載目錄 `/shared/reports/daily/` 下
2. THE Report_Directory SHALL 以角色名稱作為子目錄名稱（如 `/shared/reports/daily/bob/`、`/shared/reports/daily/puff/`）
3. THE Daily_Report SHALL 保留所有歷史紀錄，不進行自動清除
4. WHEN 任何 Agent 需要查閱其他角色的日報，THE Agent SHALL 能透過 `/shared/reports/daily/{角色名}/` 路徑直接讀取
5. WHEN 任何 Agent 需要回顧過去的工作紀錄，THE Agent SHALL 以日報作為長期記憶的查詢來源（因 Status_File 僅保留 3 天紀錄）

### 需求 7：Cronjob 設定部署

**使用者故事：** 身為系統管理者，我希望日報排程能透過現有的 cronjob.toml 機制設定，以便統一管理。

#### 驗收條件

1. THE Cronjob_Scheduler SHALL 在各 Agent 的 `.openab/cronjob.toml` 中新增日報撰寫的排程項目
2. THE Cronjob_Scheduler SHALL 使用以下設定格式：
   ```toml
   [[jobs]]
   schedule = "0 22 * * *"
   channel = "{該角色的主要頻道ID}"
   message = "撰寫今日日報"
   sender_name = "DailyReport"
   timezone = "Asia/Taipei"
   ```
3. THE Cronjob_Scheduler SHALL 將 `sender_name` 統一設定為 `"DailyReport"`，以便識別日報相關的排程任務
4. IF Agent 的 `cronjob.toml` 已有其他排程項目，THEN THE Cronjob_Scheduler SHALL 追加日報排程而不影響既有設定

### 需求 8：日報用途與價值

**使用者故事：** 身為團隊創造者（人類），我希望日報機制能提供多面向的價值，以便持續改善團隊運作。

#### 驗收條件

1. THE Daily_Report SHALL 作為長期記憶歸檔，當 Status_File 清除舊資料後，日報永久保留供回顧查詢
2. THE Daily_Report SHALL 透過「今日自我檢討」建立自我改善迴路，記錄被糾正的事與流程問題，供創造者未來提取 pattern 調整 steering
3. THE Daily_Report SHALL 支援跨角色協作感知，章魚哥（squidward）可讀取所有角色的日報以掌握團隊全局
4. THE Daily_Report SHALL 支援未來工作量分析，透過統計各角色產出量調整任務分配
5. THE Daily_Report SHALL 作為知識沉澱載體，保留技術決策原因與上下文（比 commit message 更完整）
6. WHEN 某角色連續多日無工作紀錄，THE Daily_Report SHALL 透過「今日無工作紀錄」的標註使異常狀況可被偵測
