# 實作計畫：自動日報撰寫機制

## Overview

本實作計畫將自動日報撰寫機制部署到比奇堡 AI Agent 團隊的 5 個角色（bob、patrick、puff、squidward、sandy）。核心工作為：建立共享目錄結構、撰寫日報 steering 文件、設定 cronjob 排程。

由於本功能為 AI Agent 行為規範 + 排程設定的部署，不涉及傳統程式碼開發，因此不包含 property-based testing。

## Tasks

- [x] 1. 建立共享目錄結構
  - 建立 `shared/reports/daily/` 目錄及 5 個角色子目錄
  - 每個子目錄放置 `.gitkeep` 以確保 git 追蹤空目錄
  - 目錄清單：`shared/reports/daily/bob/`、`shared/reports/daily/patrick/`、`shared/reports/daily/puff/`、`shared/reports/daily/squidward/`、`shared/reports/daily/sandy/`
  - _Requirements: 6.1, 6.2_

- [ ] 2. 撰寫日報 steering 文件
  - [x] 2.1 建立 bob 的日報 steering 文件
    - 建立 `agents/bob/.kiro/steering/daily-report.md`
    - 內容包含：觸發識別（sender_name = "DailyReport"）、資料收集步驟（讀取 _projects.md → 逐一讀取 _status.md → 執行 git log）、篩選邏輯（只取當日日期紀錄）、日報格式模板、寫入路徑（`/shared/reports/daily/bob/YYYY-MM-DD.md`）、_status.md 清理邏輯（刪除超過 3 天的紀錄）、邊界處理（無活動時產出「今日無工作紀錄」日報）、今日自我檢討引導方向
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

  - [x] 2.2 建立 patrick 的日報 steering 文件
    - 建立 `agents/patrick/.kiro/steering/daily-report.md`
    - 內容與 bob 相同結構，角色名稱替換為 patrick，寫入路徑為 `/shared/reports/daily/patrick/YYYY-MM-DD.md`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

  - [x] 2.3 建立 puff 的日報 steering 文件
    - 建立 `agents/puff/.kiro/steering/daily-report.md`
    - 內容與 bob 相同結構，角色名稱替換為 puff，寫入路徑為 `/shared/reports/daily/puff/YYYY-MM-DD.md`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

  - [x] 2.4 建立 squidward 的日報 steering 文件
    - 建立 `agents/squidward/.kiro/steering/daily-report.md`
    - 內容與 bob 相同結構，角色名稱替換為 squidward，寫入路徑為 `/shared/reports/daily/squidward/YYYY-MM-DD.md`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

  - [x] 2.5 建立 sandy 的日報 steering 文件
    - 建立 `agents/sandy/.kiro/steering/daily-report.md`
    - 內容與 bob 相同結構，角色名稱替換為 sandy，寫入路徑為 `/shared/reports/daily/sandy/YYYY-MM-DD.md`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

- [ ] 3. 設定 Cronjob 排程
  - [x] 3.1 修改 bob 的 cronjob.toml（追加日報排程）
    - 在 `agents/bob/.openab/cronjob.toml` 末尾追加日報排程項目
    - 保留既有的 YouTubeDigest 和 YouTubeDigestPush 排程不動
    - 使用 channel = `${CHANNEL_KRUSTY_KRAB}`（與 bob 的 config.toml 一致使用環境變數）
    - 設定：schedule = "0 22 * * *", message = "撰寫今日日報", sender_name = "DailyReport", timezone = "Asia/Taipei"
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3, 7.4_

  - [x] 3.2 新建 patrick 的 cronjob.toml
    - 建立 `agents/patrick/.openab/cronjob.toml`
    - 使用 channel = `${CHANNEL_KRUSTY_KRAB}`（patrick 的 config.toml 使用環境變數）
    - 設定：schedule = "0 22 * * *", message = "撰寫今日日報", sender_name = "DailyReport", timezone = "Asia/Taipei"
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3_

  - [x] 3.3 新建 puff 的 cronjob.toml
    - 建立 `agents/puff/.openab/cronjob.toml`
    - 使用 channel = `${CHANNEL_KRUSTY_KRAB}`（puff 的 config.toml 使用環境變數）
    - 設定：schedule = "0 22 * * *", message = "撰寫今日日報", sender_name = "DailyReport", timezone = "Asia/Taipei"
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3_

  - [x] 3.4 新建 squidward 的 cronjob.toml
    - 建立 `agents/squidward/.openab/cronjob.toml`
    - 使用 channel = `${CHANNEL_KRUSTY_KRAB}`（squidward 的 config.toml 使用環境變數）
    - 設定：schedule = "0 22 * * *", message = "撰寫今日日報", sender_name = "DailyReport", timezone = "Asia/Taipei"
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3_

  - [x] 3.5 新建 sandy 的 cronjob.toml
    - 建立 `agents/sandy/.openab/cronjob.toml`
    - 使用 channel = `1492090122257170526`（sandy 的 config.toml 使用硬編碼 channel ID，此為蟹堡王頻道）
    - 設定：schedule = "0 22 * * *", message = "撰寫今日日報", sender_name = "DailyReport", timezone = "Asia/Taipei"
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.2, 7.3_

- [x] 4. Checkpoint - 驗證設定完整性
  - 確認所有檔案已建立，結構正確
  - 確認 bob 的 cronjob.toml 保留既有排程且新增日報排程
  - 確認 5 個角色的 steering 文件內容完整
  - 確認 gary 和 wecom-bot 未被加入日報排程
  - Ensure all files are created correctly, ask the user if questions arise.
  - _Requirements: 1.4, 1.5_

- [x] 5. 驗證排除條件與最終確認
  - 確認 `agents/gary/` 和 `agents/wecom-bot/` 目錄下無日報相關設定
  - 確認 `/shared/reports/daily/` 目錄結構完整（5 個角色子目錄 + .gitkeep）
  - 確認所有 cronjob.toml 的 cron 表達式、timezone、sender_name 正確
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 1.4, 1.5, 6.1, 6.2, 7.2, 7.3_

## Notes

- 本功能不涉及傳統程式碼開發，核心是 AI Agent 行為規範（steering）與排程設定（cronjob.toml）
- 不使用 property-based testing，因為全是宣告式設定與自然語言指引
- steering 文件是本功能最核心的部分，需仔細設計日報撰寫流程的每個步驟
- sandy 的 channel 使用硬編碼 ID（`1492090122257170526`），其餘角色使用環境變數 `${CHANNEL_KRUSTY_KRAB}`
- 部署後需重啟容器（`docker compose restart`）才會生效，但此為運維操作不列入任務
- 各角色的 steering 內容結構相同，僅角色名稱和寫入路徑不同
