# Admin 管理後台 — Changelog

## 2026-06-09

### 新功能
- **Login 頁面改 Vue SPA** (PR #32) — 移除 Jinja2 模板，改為 Vue SPA + JSON API，前端 navigation guard
- **討論串管理增量** (PR #33) — 建立者篩選、閒置標紅修正、建議清理列表、持續性標記、閒置天數可設定、對話預覽 scroll 到底 + 自動載入、mention 人名替換
- **Config.toml 管理 UI** (PR #34) — 角色 config.toml 卡片模式 + raw TOML 編輯
- **部署管理** (PR #35) — 一鍵 Build & Deploy（git pull → docker build → k3s import → restart）、部署歷史、Git 狀態顯示
- **Log 搜尋** (PR #36) — 跨 Pod 關鍵字搜尋、時間範圍篩選、即時 tail 模式、匯出 log
- **訊息推送增強** (PR #37) — 企業微信 Webhook 推送、排程發送、推送歷史紀錄

### 修正
- 通訊管理選單 icon 亂碼修正
- 閒置標紅 CSS 判斷順序 bug
- 討論串載入前不顯示空狀態
- 角色名稱顯示中文
- 搜尋按鈕位置調整

### 安全
- `POST /api/login` 加入非法 body 解析保護
- `PUT /api/agents/{name}/config` 加入 request body 驗證
- WeCom webhook URL 限制只允許 `qyapi.weixin.qq.com`（防 SSRF）
