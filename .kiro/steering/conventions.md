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

## Docker

- AI 角色使用根目錄的 `Dockerfile`（基於官方 OpenAB image）
- 獨立服務各自有自己的 `Dockerfile` 在 `services/<name>/`
- 不要把 token 或密鑰寫死在任何檔案中，一律用環境變數

## 環境變數命名

- Bot token：`DISCORD_BOT_TOKEN_<ALIAS>`（例如 `DISCORD_BOT_TOKEN_BOB`）
- Channel ID：`CHANNEL_<NAME>`（例如 `CHANNEL_GENERAL`）
- 新增變數時同步更新 `.env.example`
