# 🏝️ 比奇堡 AI 開發團隊 — 進度追蹤

> 目標：建立多 AI Agent 協作的開發團隊，透過 Discord 交辦、GitHub 管理程式碼、Redmine 追蹤任務。

---

## ✅ 已完成

### 基礎建設
- [x] OpenAB 多 bot Docker 部署架構（bob、patrick、puff）
- [x] Dockerfile：基於 OpenAB image + git + gh CLI
- [x] docker-compose.yml：多角色服務定義
- [x] 環境變數管理：`inherit_env` 白名單機制（解決 kiro-cli 2.2.0 不繼承容器 env 問題）
- [x] 多 bot 協作配置：`allow_bot_messages=mentions` + `allow_user_messages=multibot-mentions`
- [x] 新增角色 SOP：`docs/new-agent-sop.md`
- [x] 開發慣例文件：`.kiro/steering/conventions.md`

### Git Flow
- [x] Git Flow SOP 文件：`docs/git-flow-sop.md`
- [x] 海綿寶寶 git-flow steering：`agents/bob/.kiro/steering/git-flow.md`
- [x] 派大星 git-flow steering：`agents/patrick/.kiro/steering/git-flow.md`
- [x] GitHub 認證：共用 `GH_TOKEN` 環境變數（PAT，方案 B）
- [x] 海綿寶寶能完整走 git-flow：開分支 → 開發 → push → 開 PR → mention 泡芙老師

### 泡芙老師 Code Review Agent
- [x] 角色建立（Discord bot + config.toml + steering）
- [x] 審查規則：`agents/puff/.kiro/steering/review-rules.md`
- [x] 工作流程：`agents/puff/.kiro/steering/workflow.md`
- [x] GitHub 工具指南：`agents/puff/.kiro/steering/git-tools.md`
- [x] GH_TOKEN 環境變數正確傳遞（inherit_env）
- [x] 能讀取 PR、留下結構化 review comment
- [x] 能 mention 工程師通知修正
- [x] 工程師修正後能進行第 2 輪審閱
- [x] 能略過被合理拒絕的 [建議] 項目
- [x] 通過後 mention 交辦人
- [x] Bot 互相 mention 能正確觸發回應

### Redmine MCP
- [x] MCP Server 方案選定：redmine-mcp-server（HTTP Streamable）
- [x] 海綿寶寶 MCP 連線成功（讀取 issue + 回覆留言）
- [x] MCP 部署指南：`docs/mcp-redmine-deploy.md`
- [x] MCP 連線設定參考：`docs/mcp-config-reference.md`

---

## 🔲 進行中 / 待完成

### 短期（本週）
- [ ] 章魚哥 + 派大星 Discord 連線問題排查
  - squidward：連上 Discord 但 kiro-cli ACP 斷線（`connection closed`），runtime 檔案已從 bob 複製，`allow_user_messages` 已改為 `mentions`，需再測試 mention 是否能觸發回應
  - patrick：token 被 Discord 拒絕（`Discord rejected bot token`），需去 Developer Portal 重新生成 token 並更新 `.env` 的 `DISCORD_BOT_TOKEN_PATRICK`
- [ ] 完整 Code Review 流程端到端測試
- [ ] 合併 `kiro_20260512_puff-agent` 分支到 develop

### 中期
- [ ] Redmine MCP Server 正式部署到 MCP 服務器
- [ ] 角色 `mcp.json` 改用正式環境內網 IP
- [ ] 移除 docker-compose 的 `extra_hosts`
- [ ] 派大星 Redmine 帳號 + MCP config
- [ ] Redmine + Git Flow 整合測試（issue → 開發 → PR → review → 完成）
- [ ] 調教 Redmine 任務處理流程（狀態轉換 SOP）

### 長期 / 未來規劃
- [ ] Redmine 升級 6.1 評估（OAuth2 支援，解決多帳號需多 instance 問題）
- [ ] 多角色協作場景（蟹老闆分配 issue、海綿寶寶前端、派大星後端）
- [ ] Discord Channel 情境切換（不同 channel 對應不同專案/情境）
- [ ] 更新 README.md
- [ ] GitHub 獨立帳號（解除共用 PAT 的 approve 限制）

---

## 踩坑紀錄

### kiro-cli 2.2.0 環境變數不繼承

**問題**：kiro-cli 2.2.0 改用 ACP `createTerminal` 機制建立 shell session，不再自動繼承容器環境變數。  
**解法**：在 `config.toml` 的 `[agent]` 區塊使用 `inherit_env` 白名單：
```toml
[agent]
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]
```
**原因**：安全設計，避免 `DISCORD_BOT_TOKEN` 等敏感資訊洩漏到 agent shell。

### 多 bot 同頻道搶答

**問題**：預設 `allow_user_messages=involved` 模式下，bot 參與過的 thread 中所有訊息都會觸發回應。  
**解法**：
```toml
allow_bot_messages = "mentions"          # bot 之間只回應被直接 @mention
allow_user_messages = "multibot-mentions" # 多 bot thread 中只回應被人類直接 @mention
```

### config.toml 修改後需 restart

Volume mount 的 config.toml 修改後，`docker compose up -d` 不會自動重啟容器（因為 image 沒變）。  
必須 `docker compose restart <agent>` 才會載入新 config。

### kiro-cli 連接 MCP 的必要條件

1. **MCP config**（`~/.kiro/settings/mcp.json`）— 指定 server URL 和認證
2. **不要自訂 agent config** — 用 built-in 的 `kiro_default`（有 `tools: ["*"]`）
3. **Steering 裡明確告知有 MCP 工具** — `~/.kiro/steering/mcp-tools.md` 列出可用工具
4. **MCP server 必須先啟動** — 在角色 container 啟動前
5. **Docker 容器連 host 服務** — 用 `extra_hosts: ["host.docker.internal:host-gateway"]`

---

## 進度追蹤

| 日期 | 完成項目 | 備註 |
|------|----------|------|
| 2026/04/15 | Redmine MCP POC 啟動 | 海綿寶寶帳號建立、MCP 研究 |
| 2026/04/16 | Redmine MCP 連線成功 | 改用 redmine-mcp-server（HTTP Streamable），海綿寶寶成功讀取 issue 並回覆 |
| 2026/04/16–17 | Git Flow SOP 完成 | 分支 `kiro_20260416_git-flow-sop`：SOP 文件、steering、Dockerfile 加 gh、GH_TOKEN |
| 2026/05/12 | 泡芙老師 Code Review Agent 完成 | 分支 `kiro_20260512_puff-agent`：inherit_env 解決 env 問題、多 bot 協作配置、review 流程測試通過 |
| 2026/05/12 | 移除 steering-lab | 實際未使用，直接管理 `agents/<name>/.kiro/steering/` + git 版控 |
| 2026/05/12 | 移除 entrypoint.sh | inherit_env 取代了 .bashrc workaround，Dockerfile 簡化 |
| 2026/05/12 | 工作目錄重整 | bob/patrick/puff 改為按專案分群組 + `_projects.md` + `_status.md` 取代 WORKLOG |
| 2026/05/12 | Steering 精簡 | bob 從 370 行降到 120 行（-68%），統一所有角色格式 |
| 2026/05/12 | 章魚哥（squidward）建立 | PM 角色，config + steering + 專案文件（ALS 客訴完整規格已轉入） |
| 2026/05/12 | Kiro CLI API Key 設定 | 每角色獨立 key，docker-compose 映射為統一 `KIRO_API_KEY` |
| 2026/05/12 | Channel 分配 | 新增蟹堡王/會議室/電視台/回報站/實驗室，各角色按職責分配 |
| 2026/05/12 | Bot Setup SOP | `docs/bot-setup-sop.md` 含模板和 token 預算規範 |
