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
- [x] 章魚哥 + 派大星 Discord 連線問題排查（已解決，兩者皆正常運作中）
- [x] 完整 Code Review 流程端到端測試
- [x] 合併 `kiro_20260512_puff-agent` 分支到 develop

### 中期
- [x] Redmine MCP Server 正式部署到 MCP 服務器
- [x] 角色 `mcp.json` 改用正式環境內網 IP
- [x] 移除 docker-compose 的 `extra_hosts`
- [x] 派大星 Redmine 帳號 + MCP config
- [x] Redmine + Git Flow 整合測試（issue → 開發 → PR → review → 完成）
- [x] 調教 Redmine 任務處理流程（狀態轉換 SOP）

### 短期（優先）
- [x] **升級 OpenAB 0.8.4** — Trusted bot @mention bypass involvement gate，改善 multi-agent 協作（bot 互 mention 不再被擋）
  - ✅ 改 Dockerfile `FROM ghcr.io/openabdev/openab:0.8.4`
  - ✅ 設定各 bot 的 `trusted_bot_ids`
  - ⚠️ 測試發現 Discord Gateway 不推送 bot-to-bot mention 給非 thread member 的 bot（OAB 已知限制，缺少 auto-join thread）
  - **Workaround**：人類開 thread 時 mention 群組 role 一次拉入所有 bot，之後 bot 互 mention 正常運作
  - 等待 OAB 未來版本加入 `thread_create` handler 自動 join thread
- [ ] **OpenAI Usage 查詢 — 環境變數設定**（程式碼已完成，待設定 env）
  - ⬜ 到 OpenAI Platform → Admin keys 建立 Admin API Key
  - ⬜ 在 `.env` 設定 `OPENAI_ADMIN_KEY=sk-admin-xxxxx`
  - ⬜ 在 `.env` 設定 `OPENAI_ORG_ID=org-xxxxx`（選填，單 org 可不填）
  - ⬜ 在 Discord 測試 `/openai-usage` 指令

### 長期 / 未來規劃
- [ ] **海超人首次成功部署**（待 GitHub PAT → 註冊 self-hosted runner → 建 docker-compose → 首次部署測試）
- [ ] **K3s 遷移**（分支 `feat/k3s-migration` 已備妥）— 等新桌機到後執行
  - ✅ 維運指南 + 插畫：`docs/k3s-operations-guide.md`
  - ✅ 遷移規劃：`docs/k3s-migration-plan.md`
  - ✅ 安裝腳本：`scripts/k3s-setup.sh`
  - ✅ K8s YAML：`k3s/` 目錄（namespace、configmaps、volumes、9 個 deployments）
  - ✅ 切換腳本：`scripts/k3s-cutover.sh`
  - ✅ Kiro IDE steering 指引：`.kiro/steering/k3s-migration.md`
  - ⬜ 等新桌機 Ubuntu Desktop 到 → 在新機跑設置 → 切換（預計停機 5~10 分鐘）
- [ ] **OpenAB Lifecycle Hooks (pre_boot)** — 用 `[hooks.pre_boot]` 取代 entrypoint-wrapper.sh，等 K3s 遷移完成後再做
- [ ] Skill 遷移評估（見下方計畫）
- [ ] WeCom（企業微信）Bot 接入（分支 `feat/wecom-bot` 已建立基礎架構，待企業微信應用設定）
  - 參考 PR: https://github.com/openabdev/openab/pull/769
  - 需要：企業微信自建應用 + HTTPS 回調 URL + Gateway 部署
  - 設定指南：`docs/wecom-setup.md`
  - **群聊支援**（企業已完成實名認證 ✅）：
    - 自建應用可加入群聊，群內 @應用名 觸發回調（帶 `ChatId` 欄位）
    - Gateway 已支援 `group_require_mention` 設定（預設只回應 @mention）
    - 回覆用 `appchat/send` API 指定 chatid 發送到群
    - 應用場景：業務群報價查詢、客訴快速回報、專案進度查詢、HR 公告互動
    - 注意：群成員須在應用「可見範圍」內；無 thread 隔離，同群共享上下文
  - **🔄 方向調整（2026/06/08）**：考慮將 WeCom Bot 應用轉型為專門處理特定工作的 Bot 服務
    - 不走通用 AI Agent 對話模式，改為針對特定業務場景的專用 Bot
    - 例如：報價查詢 Bot、客訴回報 Bot、HR 請假 Bot 等，各司其職
    - 優勢：回應更精準、流程更可控、不需複雜的上下文管理
    - **獨立專案命名**：不沿用比奇堡（bikini-bottom）世界觀，改用貼近工作專業的名稱
    - 待確認：專案名稱、具體要做哪些專用 Bot、架構是否共用 Gateway 還是各自獨立
- [x] Redmine 升級 6.1 評估（OAuth2 支援，解決多帳號需多 instance 問題）
- [x] 多角色協作場景（由章魚哥分配 issue，運作良好）
- [x] Discord Channel 情境切換（不同 channel 對應不同專案/情境）
- [ ] **未來角色規劃**（待需求明確後建立）：
  - **大洋遊俠 (Barnacle Boy)** — QA / 深度測試。海超人部署完後接手做完整 API 測試、E2E 流程驗證、持續監控。與海超人搭檔。
  - **皮老闆 (Plankton)** — 資安相關。程式碼安全審查、弱點掃描、權限管理稽核。
  - **蟹老闆 (Mr. Krabs)** — 效益成本分析。雲端費用監控、資源使用報告、ROI 評估。
- [x] 更新 README.md（角色清單、頻道配置、目錄結構）

---

## 📋 Skill 遷移評估計畫

### 背景

目前 Code Review、Git Flow、Redmine 相關的知識分散在各角色的 steering 裡（bob/patrick/puff 各有一份）。評估是否值得移轉為共用 Skill 放到 `KedingTW/agent-skills` repo。

### 評估標準

轉為 Skill 的條件（同時滿足）：
1. **多角色共用** — 超過 2 個角色需要同樣的知識
2. **不常變動** — 規則穩定，不需要每週調整
3. **按需載入有價值** — 不是每次對話都需要，只在特定情境觸發

### 評估結果

| 候選項目 | 目前位置 | 共用性 | 穩定性 | 按需價值 | 結論 |
|----------|----------|--------|--------|----------|------|
| Git Flow 規範 | bob/patrick steering | 高（所有工程師） | 高 | **低** — 幾乎每次開發都要用 | ❌ 保留 steering |
| Code Review 規則 | puff steering | 低（只有泡芙） | 高 | 低 — 泡芙每次都要用 | ❌ 保留 steering |
| GitHub 工具指南 | puff steering | 低（只有泡芙） | 高 | 低 | ❌ 保留 steering |
| Redmine MCP 操作 | bob steering | 中（bob + 未來其他角色） | 高 | **高** — 不是每次都需要 | ⚠️ 待觀察 |

### 結論

**目前不遷移**。原因：

1. **Git Flow** — 工程師幾乎每次任務都需要，放 steering（always loaded）比 skill（on-demand）更合適。而且 bob 和 patrick 的版本有細微差異（角色名稱、流程終點描述），不適合完全統一。

2. **Code Review** — 只有泡芙需要，且她每次被 mention 都是在做 review，放 steering 等於零浪費。轉 skill 反而多一步「判斷是否載入」。

3. **GitHub 工具指南** — 同上，泡芙專用。

4. **Redmine MCP** — 目前只有 bob 在用（17 行），內容很少。等更多角色需要 Redmine 操作、且內容擴充到值得獨立管理時再遷移。

### 未來觸發遷移的時機

- 新增第 3 個以上角色需要 Redmine 操作 → 建立 `redmine-ops` skill
- Git Flow 規範要大改（例如改用 trunk-based）→ 建立 `git-flow` skill 統一管理
- Code Review 規則要給外部 repo 使用（不只 bikini-bottom）→ 建立 `code-review` skill

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

### Discord Thread 中 bot-to-bot mention 不觸發

**問題**：升級 OpenAB 0.8.4 並設定 `trusted_bot_ids` 後，Bot A 在 thread 中 @mention Bot B，Bot B 完全沒反應。Log 顯示 Bot B 的 Gateway 根本沒收到該訊息事件。但同一 thread 中人類的訊息 Bot B 能正常收到。  
**根因**：Discord Gateway 的 thread subscription 機制——bot 不是 thread member 時，即使被 @mention，如果 mention 來自另一個 bot，Gateway 不會推送 MESSAGE_CREATE。人類的 mention 則會正常推送。OpenAB 0.8.4 沒有實作 `thread_create` handler 來自動 join thread。  
**確認方式**：`RUST_LOG=openab=debug,serenity=debug`，觀察 Bot B 的 log 在 Bot A mention 時完全空白。  
**Workaround**：  
1. 人類開 thread 時 mention 群組 role（如 `@比奇堡前端組`），一次把所有 bot 拉入 thread member  
2. 或人類先 mention Bot B 一次（讓 Bot B 回覆後成為 thread member），之後 Bot A 的 mention 就能正常送達  
**長期**：等 OAB 加入 `thread_create` event handler，自動 join allowed_channels parent 下的新 thread。

---

## 進度追蹤

| 日期 | 完成項目 | 備註 |
|------|----------|------|
| 2026/06/02 | OpenAB 0.8.4 升級 + trusted_bot_ids | Dockerfile 升版、8 個角色設定 trusted_bot_ids，bot 互 mention bypass involvement gate |
| 2026/06/02 | K3s 遷移規劃完成 | 維運指南、安裝腳本、K8s YAML、切換腳本、Kiro steering 指引（分支 feat/k3s-migration） |
| 2026/06/02 | README 插畫 + TODO 清理 | 團隊主視覺、工作流程、會議室插畫；清理已完成的短期/中期項目 |
| 2026/06/02 | 外部 Skill Sync 機制 | sync-skills.sh + skills.json + company-kb 掛載完成 |
| 2026/06/02 | 海超人 (Mermaid Man) 上線 | DevOps 部署執行者，角色已上線可互動。部署功能待 GitHub PAT + 首次部署完成。章魚哥 workflow 已更新交接規則。 |
| 2026/06/02 | 全角色 trusted_bot_ids 統一 | 9 個角色互相 mention 無限制 |
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
| 2026/05/13 | README 更新 | 角色清單加入章魚哥/泡芙老師、新增 Discord 頻道架構圖、目錄結構更新 |
| 2026/05/13 | Discord 頻道文件 | `docs/discord-channels.md` 記錄 6 個頻道名稱與主題 |

---

## Agent 分組管理（2026/06/10）

### 現狀

| 組別 | 平台 | 目錄 | 狀態 |
|------|------|------|------|
| 比奇堡團隊 | DC | `agents/` 根目錄（下班時間搬到 `agents/bikini-bottom/`） | ✅ 運作中 |
| 科定AI服務 | DC (新伺服器) | `agents/keding-dc/` | 🔧 建設中 |
| 科定WeCom | WeCom | `agents/keding-wecom/` | ⏸ 暫停 |

### 科定AI服務 (DC) — 伺服器資訊

- Guild ID: `1513867618899988480`
- 第一個 bot：下單小幫手
  - Bot ID: `1514058459585445888`
  - Channel: `1513867725242503168`
  - Agent: `agents/keding-dc/order-transform/`
  - Deployment: `k3s/deployments/keding-dc-order-transform.yaml`

### 待辦

- [ ] K3s secret `keding-dc-secrets` 加入 bot token
- [ ] K3s secret `kiro-api-keys` 加入 `KEDING_DC_ORDER_TRANSFORM` key
- [ ] 部署 `keding-dc-order-transform` 並驗證
- [ ] WeCom `wecom-bot-order-transform` 的 K3s deployment replicas 設 0（暫停）
- [ ] 比奇堡 agents 搬到 `agents/bikini-bottom/`（下班時間，需改所有 deployment path）
- [ ] Admin 後台支援分組顯示（未來）

  - 功能：在 DC 中 `/restart <agent>`、`/logs <agent>`、`/status` 等指令操作 K3s pod
  - 保留在比奇堡 DC 伺服器
  - 待 K3s 搬遷穩定後實作

- [ ] **架構隔離重構** — 三組 bot 完全解耦，避免改 A 壞 B
  - 現況問題：
    - 共用 Dockerfile（entrypoint-wrapper.sh 邏輯混雜 NAS/steering/skills）
    - 共用 K3s namespace（bikini-bottom）
    - 共用 image tag（bikini-bottom/agent:latest）
    - 改 entrypoint 會影響所有組
  - 目標：
    - 每組獨立 Dockerfile + image（或至少獨立 entrypoint）
    - 科定 bot image 精簡（不裝 pandoc/openpyxl/gh 等）
    - 清楚的目錄隔離：`agents/bikini-bottom/`、`agents/keding-dc/`、`agents/keding-wecom/`
    - K3s deployment 互不影響（可考慮分 namespace，但非必要）
  - 短期解法（已做）：
    - `scripts/entrypoint-minimal.sh` 給科定 bot 用
    - keding-dc deployment 用 `command` 覆蓋 entrypoint
    - 不掛 `/opt/steering`、`/opt/skills`
  - 長期方案（待規劃）：
    - `Dockerfile.keding` 獨立 image
    - 或改用 multi-stage build + build arg 選 entrypoint
    - 管理工具統一（admin 分組顯示、分組操作）
