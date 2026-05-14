---
inclusion: manual
---

# 開發慣例

## 語言

- 所有文件、註解、commit message 使用繁體中文
- 角色的 steering 檔案全程繁體中文，不使用英文
- 程式碼中的變數名和技術術語可以用英文

## 角色管理

- 每個角色一個獨立目錄在 `agents/<alias>/`
- 角色別名使用英文小寫（bob, patrick, gary, krabs, squidward, sandy, plankton）
- 新增角色遵循 `docs/new-agent-sop.md`
- 角色的 config.toml 中使用 `${ENV_VAR}` 引用環境變數，實際值放 `.env`
- 所有 bot 的 Discord 配置統一設定：
  - `allow_bot_messages = "mentions"` — bot 之間只回應被直接 @mention 的訊息（支援 bot 互相呼叫）
  - `allow_user_messages = "multibot-mentions"` — 多 bot thread 中只回應被人類直接 @mention 的訊息（避免搶答）

## Docker

- AI 角色使用根目錄的 `Dockerfile`（基於官方 OpenAB image）
- 獨立服務各自有自己的 `Dockerfile` 在 `services/<name>/`
- 不要把 token 或密鑰寫死在任何檔案中，一律用環境變數

## 環境變數管理

### inherit_env 機制（重要）

kiro-cli 2.2.0+ 使用 ACP 協議建立 shell session，**不會自動繼承容器環境變數**。
必須在 `config.toml` 的 `[agent]` 區塊明確列出需要傳遞的環境變數：

```toml
[agent]
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]
```

**規則：**
- `inherit_env` 是白名單機制，只有列出的變數才會傳入 agent 的 shell session
- 敏感但 agent 不需要的變數（如 `DISCORD_BOT_TOKEN`）不要列入
- 新增環境變數時，必須同時更新 `config.toml` 的 `inherit_env` 列表，否則 agent 看不到

### 新增環境變數 SOP

1. 在 `.env` 新增變數值
2. 在 `.env.example` 新增範例
3. 在 `docker-compose.yml` 對應 service 的 `environment` 區塊新增
4. **如果 agent 的 shell 需要用到**：在該 agent 的 `config.toml` 的 `inherit_env` 列表中新增
5. 重新啟動容器：`docker compose up -d --build <agent>`

### 命名規則

### 命名規則

- Bot token：`DISCORD_BOT_TOKEN_<ALIAS>`（例如 `DISCORD_BOT_TOKEN_BOB`）
- Channel ID：`CHANNEL_<NAME>`（例如 `CHANNEL_KRUSTY_KRAB`）
- 新增變數時同步更新 `.env.example`

## Git

- 分支策略：`master`（正式）+ `develop`（開發），一般開發對 `develop` 開 PR，hotfix 同時對 `master` 和 `develop` 開 PR
- 分支命名格式：`<角色別名>_<YYYYMMDD>_<簡短描述>`
  - Kiro IDE：`kiro_<YYYYMMDD>_<描述>`
  - Agent：`<別名>_<YYYYMMDD>_<描述>`（例如 `bob_20260416_fix_null_check`）
- 簡短描述使用英文小寫，多個單字用 `_` 連接
- commit message 使用繁體中文，格式：`feat/fix/chore/docs: 簡短描述`，可附多行說明
- PR 標題與分支名相同
- 不直接 push 到 master 或 develop
- Agent 不可自行合併 PR，由主管合併
- GitHub 認證使用共用 `GH_TOKEN`（PAT），透過環境變數注入
- 完整流程參考 `docs/git-flow-sop.md`
