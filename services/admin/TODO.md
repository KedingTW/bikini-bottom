# Admin 管理後台 — TODO

## 選單結構重整
- [x] 拆開 Discord 頁面成獨立選單項目
- [x] 新選單結構：
  ```
  🏠 總覽
  📊 資源監控（主機 + Pod）
  💰 成本監控
  🔔 異常通知紀錄
  ─── 通訊管理 ───
  💬 訊息推送（DC + WeCom）
  👥 成員管理（DC 成員 + 身分組）
  📌 討論串管理（列表/篩選/批次操作/結案）
  📈 討論串分析（活躍度/自動化指數）
  ─── AI 角色管理 ───
  🤖 角色配置（MCP/Skills/Steering）
  ⏰ Cronjob 管理
  📚 Knowledge Base
  ─── 系統運維 ───
  🖥️ 系統資源（主機 CPU/RAM/Disk）
  📋 Log 搜尋（跨 Pod）
  🚀 部署管理（Build & Deploy + 歷史）
  🔑 API Key 管理
  ─── 系統管理 ───
  👤 使用者管理
  ```

---

## 通訊管理

### 討論串管理（核心）
- [ ] 排序：按最後活動時間（最久未動優先）
- [ ] 篩選：按標籤/頻道/建立者
- [ ] 批次結案：貼「已完成」/「已結案」標籤 + 移除「處理中」「測試中」
- [ ] 批次封存：結案 + 封存 thread
- [ ] 閒置提醒：超過 N 天未動作標黃/標紅
- [ ] 建議清理列表（閒置 thread 一覽）
- [ ] 排程/持續性 thread 標記（不建議關閉）
- [ ] 勾選多個一起操作

### 討論串分析
- [ ] 每人發起的 thread 數統計
- [ ] 平均解決時間（建立到封存）
- [ ] 自動化指數全體平均
- [ ] 標籤分佈圓餅圖

### 成員管理
- [ ] 批次加/移除身分組
- [ ] 成員活躍度（最常發言排名）

### 訊息推送
- [x] Discord 發公告（已完成 ✅）
- [ ] 排程發送（定時推送）
- [ ] WeCom 推送
- [ ] 推送歷史紀錄

---

## AI 角色管理

### 角色配置
- [x] MCP 配置：UI 管理（啟用/停用/新增/刪除）+ JSON raw mode 編輯（含語法驗證）
- [x] Skills：列出 skill + 描述，可預覽 SKILL.md（唯讀，透過 Kiro 修改）
- [x] Steering：列表預覽（唯讀，透過 Kiro 修改）
- [x] Cronjob 視覺化管理：每個 job 顯示 schedule/sender/channel/timezone + 一鍵啟用/停用 + TOML raw 編輯
- [x] Knowledge Base 管理：讀 contexts.json 顯示人類可讀名稱、來源檔案、大小，點開預覽 source_path
- [x] Dialog 固定高度（80vh）+ 卡片 4 欄佈局 + URL hash 同步
- [ ] Config.toml：agent 基本設定
- [ ] 配置比對（A 角色 vs B 角色差異）
- [ ] 範本套用（一次套用 MCP 配置到多個角色）
- [ ] KB 上傳新檔案
- [ ] Cronjob 手動觸發（不等排程）
- [ ] Cronjob 執行歷史

---

## 系統運維

### 系統資源
- [ ] 主機 CPU / RAM / Disk 即時用量
- [ ] 歷史趨勢圖（搭配 SQLite 記錄）
- [ ] 磁碟空間警告

### Log 搜尋
- [ ] 跨 Pod 搜尋關鍵字
- [ ] 時間範圍篩選
- [ ] 即時 tail -f 模式
- [ ] 匯出 log

### 部署管理
- [ ] 一鍵 Build & Deploy（選角色 → build image → import → restart）
- [ ] 搭配 bot bootstrap 流程
- [ ] 部署歷史 / Change Log（誰在什麼時間做了什麼）
- [ ] Git 狀態顯示（branch / 最近 commit / uncommitted changes）

### API Key 管理
- [ ] 列出所有服務的 API Key（遮罩顯示）
- [ ] Key 到期時間 / 用量追蹤
- [ ] 新增/輪替 key 提醒

---

## 報表 & 匯出

- [ ] 團隊週報/月報自動彙整
- [ ] 匯出 PDF / Excel
- [ ] 內容：Kiro 用量 + OpenAI 費用 + 討論串進度 + bot 活躍度

---

## WeCom Bot 管理（未來）
- [ ] 訊息推送整合
- [ ] 成員管理
- [ ] 對話紀錄

---

## UI/UX 改善
- [ ] Login 頁面改 Vue（移除 templates/login.html + Jinja2，登入流程改 SPA + JSON API，視覺風格統一）
- [ ] .gitignore 整理（目前累積太多片段，需重新分類整合）
- [ ] Kiro 額度 tab 改版（摘要卡片 + 每日趨勢）
- [ ] 圖表 hover 優化
- [ ] 響應式（手機/平板）調整
- [ ] 操作日誌（誰在後台做了什麼）

---

## 倉儲清理（Repo Hygiene）
- [ ] 歷史 commit 中的 SSH 私鑰 (`agents/squidward/.ssh/BikiniBottom.pem`) — 用 git-filter-repo 重寫歷史；同時撤換 AWS key pair
- [ ] 歷史 commit 中的 MCP Bearer token (`mcp-backup/`) — 同上，並輪替 token
- [ ] 角色私有檔案備份機制（spec/筆記等不該進團隊 repo，但需要備份）
