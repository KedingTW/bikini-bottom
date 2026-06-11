# 🏝️ 比奇堡 AI 開發團隊 — Changelog

> 時間越新越靠上方。紀錄團隊基礎設施、角色、流程的所有變更。

---

## 2026-06-11

- **feat**: 小蝸（gary）角色升級為專案經理（PM）— 與章魚哥完全相同職責，移除原本的維運助手/usage report 定位
- **docs**: 更新 overview、team-announcement、usage-guide、discord、project steering 等文件，反映小蝸的新角色
- **docs**: 更新 daily-report spec，將 gary 加入日報撰寫排程

## 2026-06-09

- **feat**: 角色配置（AgentConfig）大幅強化 — 卡片改 4 欄+細項統計（MCP 啟用/總數、技能、指引、排程啟用/總數、KB context 數）、Dialog 固定 85vh
- **feat**: Cronjob 視覺化管理 — 列出每個 job（schedule/channel/sender/timezone）、一鍵啟用/停用、保留 TOML raw editor（雙模式切換）
- **feat**: Knowledge Base 管理 — 從 `contexts.json` 讀人類可讀名稱、source_path、item_count、size，點開可預覽來源檔內容
- **feat**: Skills 顯示修正 — admin 容器掛載 `/opt/skills`，符號連結正確解析；卡片顯示 SKILL.md frontmatter description，點開預覽
- **feat**: AgentConfig 與總覽 URL hash 同步 — `/agent-config#bob` 自動彈 dialog
- **fix**: 小蝸（gary）Dashboard 狀態偵測修正（name mapping gary → gary）
- **feat**: Admin 管理後台全面升級 — dashboard 更名為 admin，重構為 Vue 3 + Vite + Tailwind 標準專案
- **feat**: 總覽頁 — 角色狀態卡片（按記憶體排序）、CPU/Memory 即時監控、告警橫幅
- **feat**: 資源監控 — 每角色歷史 CPU/Memory 圖表（SQLite 紀錄，保留 30 天）、放大 Dialog
- **feat**: 成本監控 — Kiro 額度排名 + OpenAI 費用分析（每日趨勢圖、按模型拆分、Token 用量）
- **feat**: 成本監控快取 — Kiro 1 小時 / OpenAI 30 分鐘，點更新強制重查
- **feat**: 告警系統 — 自動偵測 OOMKilled/CrashLoopBackOff/重啟，告警紀錄歷史頁面
- **feat**: Discord 管理 — 成員列表（中文名對照）、身分組管理（過濾 bot 角色）、發送公告
- **feat**: 討論串管理 — 列表/標籤篩選/封存、活躍度分析（每日新增折線圖）
- **feat**: 討論串詳情 — 每小時對話密度圖、自動化指數、參與者統計
- **feat**: 使用者管理 — 新增/刪除/重設密碼/角色切換（admin/viewer）
- **feat**: 修改密碼功能 + 右上角下拉選單
- **feat**: 左側收合選單 + 分組顯示 + sticky bar + 深海鳳梨背景
- **feat**: 選單重整 — 通訊管理/AI 角色/系統運維分組，未實作頁面顯示 Coming Soon
- **chore**: AGENTS display 移除 emoji prefix
- **chore**: 新增 conch avatar、assets 品牌資源（header/footer/logo）
- **chore**: 新增 DISCORD_BOT_TOKEN_KAREN 到 .env

## 2026-06-04

- **feat**: K3s 遷移完成 — 全部 agent deployment 的 hostPath 改為直接讀取 repo 目錄，不再依賴 `/opt/bikini-bottom` 副本，等同 docker-compose 的 bind mount 行為
- **feat**: 新增 dashboard service 部署到 K3s（NodePort 30080）
- **chore**: gary 正式改名為 gary（deployment、image、secret 統一命名）
- **feat**: 小蝸新增 `/openai-usage` 指令 — 查詢 OpenAI API 費用與 token 用量（使用 Admin API Key）
- **feat**: 同步 agent-skills repo 全部 skills — 新增 kd-company-knowledge、kd-complaint-handler、kd-crm-operations、kd-glossary、kd-meeting-updates、kd-pricing-assistant、kd-product-coding、kd-product-knowledge、kd-ai-workflow-design、als-vue-ui-guide 共 10 個 skill
- **feat**: 角色 × Skill 分配策略 — kd-* 系列全員可用；kd-ai-workflow-design 僅章魚哥+珊迪；als-vue-ui-guide 僅海綿寶寶
- **docs**: README 新增角色×Skill 分配對照表，bot-setup-sop 更新可用 Skills 清單

## 2026-06-03

- **chore**: GitHub 帳號切換 — 全部 agent 改用共用帳號 `keding-bikini-bottom`

## 2026-06-02

- **feat**: 升級 OpenAB 0.8.4 + 設定 `trusted_bot_ids`（全 8 角色）— bot 互 mention bypass involvement gate（受限於 Discord thread 推送機制，需人類先拉 bot 進 thread）
- **feat**: K3s 遷移規劃完成 — 維運指南、安裝腳本、K8s YAML、切換流程（分支 `feat/k3s-migration`）
- **docs**: README 新增團隊主視覺、工作流程、會議室協作插畫
- **docs**: TODO 清理已完成項目（Discord 連線、Code Review、Redmine 等）
- **chore**: 清理專案多餘目錄 — 刪除已廢棄的 `services/magic-conch/`、冗餘的 `docs/usage-guide.html`、過時的 `agents/magic-conch/`（spec.md 搬到 `agents/conch/`）

## 2026-06-01

- **feat**: 新增 Karen — Discord token holder，用於 MCP Server 管理
- **fix**: PR title 規則統一用自己的角色名稱，不再用交辦人名稱

## 2026-05-28

- **misc**: 更新 gitignore、env example、steering、avatars、specs

## 2026-05-27

- **feat**: 神奇海螺升級為 OpenAB agent + 容器管理指令搬給小蝸（gary）
- **feat**: 新增珍珍（Pearl）和蝦霸（Larry）兩位開發者 agent
- **fix**: README 目錄結構補上 `agents/conch/`
- **chore**: 整理先前未推送的設定更新和文件

## 2026-05-22

- **docs**: PR title 改用交辦人名稱
- **chore**: NAS CIFS 加入容錯參數（echo_interval、cache=loose）

## 2026-05-21

- **feat**: 新增共用 Skills 機制（xlsx, pdf, pptx, docx, doc-coauthoring）
- **feat**: 新增身分組機制、安全規則、修正 mention 流程
- **feat**: 更新筱瓔資訊 — 董事長秘書角色定義 + 互動態度規則
- **chore**: 升級 OpenAB 從 0.8.3-beta.5 到 0.8.3 stable
- **fix**: 筱瓔職稱更新 + 校正互動規則

## 2026-05-20

- **feat**: 遷移 shared & projects 到 NAS（單一 CIFS volume 掛載 `88.BikiniBottom`）

## 2026-05-19

- **feat**: 升級 OpenAB 至 0.8.3-beta.5，啟用 `allowed_role_ids` 身分組觸發
- **feat**: 新增前端組/後端組身分組
- **refactor**: PR 審核流程改為泡芙直接在原 thread mention 人類審核者
- **refactor**: 統一 steering 共用文件，修正時區與 git 規則
- **fix**: 改 `allow_user_messages` 為 `mentions` 解決 thread 首次 mention 不回應問題
- **fix**: 泡芙加入訊息分流判斷，防止收到開發需求時自行寫程式碼
- **chore**: 移除 `[bot-meta]` 機制
- **chore**: 新增成員小美女

## 2026-05-18

- **feat**: 新增神奇海螺（Magic Conch）服務 — Discord bot 管理與容器操控
- **feat**: `/conch-archive` 指令 — thread 封存機制
- **feat**: PR 審核改由工程師到電視台 mention 潔庭/詠仁
- **feat**: 強化交棒 mention 機制 + 三階段 PR 審核流程
- **feat**: 更新團隊組織架構 — 新增珈瑄、詠仁、潔庭
- **feat**: bob/patrick 加入電視台 API 推訊息流程
- **refactor**: rename `agents/conch` → `agents/magic-conch`
- **docs**: thread 封存機制設計文件

## 2026-05-15

- **feat**: 所有 bot 加入 `max_bot_turns = 100` 設定
- **feat**: 加入角色頭像 + .gitignore 排除 runtime 檔案
- **docs**: 新增交棒規則、跨頻道交接協議
- **docs**: 更新 usage-guide 加入完整團隊角色與多種工作流程
- **fix**: `/usage` 顯示升級後的正確訂閱方案

## 2026-05-14

- **feat**: 新增珊迪（Sandy）— Customer Success Manager agent
- **feat**: 新增 shared drop 目錄（bot 間檔案交換）
- **docs**: 更新 bot-setup-sop、README directory structure
- **chore**: 重組 `.env.example` 按類別分類

## 2026-05-13

- **feat**: 新增 WeCom bot + gateway scaffold（WIP）
- **feat**: workspace 重整 + 章魚哥 PM 角色建立 + Kiro API Key 認證
- **fix**: 修正章魚哥 UID + 改用 `multibot-mentions` 模式
- **docs**: 新增 WeCom Bot 規劃至 TODO（含群聊應用場景）
- **docs**: 更新使用文件

## 2026-05-12

- **feat**: 建立泡芙老師（Mrs. Puff）Code Review Agent
- **feat**: 整合泡芙老師 Code Review 流程 — 能讀取 PR、留結構化 review comment、mention 工程師通知修正
- **fix**: 解決 kiro-cli 2.2.0 環境變數不繼承問題（`inherit_env` 白名單機制）
- **fix**: 統一多 bot 協作配置（`allow_bot_messages=mentions` + `multibot-mentions`）
- **chore**: 移除 entrypoint.sh，簡化 Dockerfile
- **chore**: 移除 steering-lab 實驗框架
- **chore**: Steering 精簡 — bob 從 370 行降到 120 行（-68%）
- **chore**: 泡芙阿姨統一改名為泡芙老師
- **docs**: 全面重寫 TODO.md、新增團隊使用指南 `usage-guide.md`

## 2026-04-16 ~ 04-17

- **feat**: GitHub 認證改用 GH_TOKEN 環境變數（共用 PAT）
- **feat**: 建立 Git Flow SOP 與 steering 實驗框架
- **feat**: Redmine MCP POC — 換用 redmine-mcp-server，海綿寶寶成功讀取 issue 並回覆
- **fix**: Git Flow 與 Redmine 解耦，改為獨立流程
- **chore**: 移除 steering 中「人類」用語、review 改為等待確認/驗收
- **docs**: 同步更新 conventions、new-agent-sop、TODO

## 2026-04-15

- **feat**: gary 重構 — `/usage` 額度報表 + `/activity` 功能分析
- **chore**: 移除 AWS_SESSION_TOKEN 改用 IAM User 長期金鑰
- **chore**: steering 改為手動載入，節省 usage
- **docs**: 新增 gary IAM 最小權限 policy
- 🎉 **First commit** — 比奇堡 AI 開發團隊誕生

## 2026-06-10

- **feat**: 科定AI服務 (DC) 上線 — 第一個 bot「下單小幫手」（訂單資料轉換）
  - 新 DC 伺服器 `1513867618899988480`，Forum 頻道模式
  - Agent: `agents/keding-dc/order-transform/`
  - 使用 `entrypoint-minimal.sh`（不做 NAS/steering/skills link）
  - 權限控制：管理員（馥寧 + 米哥）可訓練，一般同事只能用
  - 糾正紀錄機制：同事指出錯誤 → 記錄 → 待馥寧確認
- **feat**: WeCom Bot 基礎架構完成（gateway 部署到 Zeabur `kd-wecom` project）
  - 通過 WeCom callback 驗證 + 成功收發訊息
  - 因缺乏表情反應體驗差，**暫停使用**，改走 DC 方式
- **refactor**: Agent 目錄分組
  - `agents/keding-dc/` — 科定AI服務
  - `agents/keding-wecom/` — 科定WeCom（暫停）
  - 比奇堡 agents 待搬到 `agents/bikini-bottom/`（下班時間）
- **refactor**: 文件拆分
  - `README.md` 改為精簡索引頁
  - `docs/bikini-bottom-overview.md` — 比奇堡總覽
  - `docs/bot-setup-sop.md` 改為索引頁 → 指向各組 SOP
  - `docs/bot-setup-sop-keding-dc.md` — 科定DC 新增 bot 完整步驟
  - `docs/keding-dc-setup.md` — 伺服器設定文件
- **refactor**: `.env.example` 重新命名分組（`BIKINI_BOTTOM_*` / `KEDING_DC_*` / `KEDING_WECOM_*`）
- **feat**: `scripts/entrypoint-minimal.sh` — 精簡 entrypoint（不做 NAS/steering/skills link）
- **feat**: `services/zeabur-gateway/` — Zeabur gateway 模組化管理工具（BotConfig / ZeaburClient / deploy scripts）
- **chore**: 移除地端 gateway deployment（改用 Zeabur）
- **fix**: K3s `kustomization.yaml` 修正 dashboard.yaml → admin.yaml 引用
