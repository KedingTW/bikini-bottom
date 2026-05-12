# 新增角色 SOP

## 前置準備

1. 到 [Discord Developer Portal](https://discord.com/developers/applications) 建立新的 Application
2. 設定 Bot 名稱和頭像
3. Bot → 開啟 **Message Content Intent**
4. OAuth2 → URL Generator → scope: `bot` → 勾選權限：
   - Send Messages
   - Send Messages in Threads
   - Create Public Threads
   - Read Message History
   - Add Reactions
   - Manage Messages
5. 用產生的連結邀請 bot 到你的 Discord server
6. 複製 Bot Token

## 建立角色目錄

以新增「蟹老闆」(krabs) 為例：

```bash
mkdir -p agents/krabs/.kiro/steering
```

## 建立設定檔

建立 `agents/krabs/config.toml`：

```toml
[discord]
bot_token = "${DISCORD_BOT_TOKEN}"
allowed_channels = ["${CHANNEL_GENERAL}"]
allow_bot_messages = "mentions"
allow_user_messages = "multibot-mentions"

[agent]
command = "kiro-cli"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent/projects"
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]

[pool]
max_sessions = 10
session_ttl_hours = 24

[reactions]
enabled = true
remove_after_reply = false

[reactions.emojis]
queued = "👀"
thinking = "🤔"
tool = "🔥"
coding = "🦀"
web = "⚡"
done = "🆗"
error = "😱"

[reactions.timing]
debounce_ms = 700
stall_soft_ms = 10000
stall_hard_ms = 30000
done_hold_ms = 1500
error_hold_ms = 2500
```

可自訂 `coding` emoji 為角色代表符號。

## 建立 Steering 檔案

### personality.md（必要）

建立 `agents/krabs/.kiro/steering/personality.md`，包含：

- 身份描述
- 個性與回答風格
- 口頭禪與用語
- 工作職責
- 互動規則
- 工作環境（固定內容，複製即可）

工作環境區塊（每個角色都一樣）：

```markdown
## 工作環境

- 你的工作目錄是 `/home/agent/projects`，所有專案都必須在這個目錄底下進行
- 每個專案用獨立的子目錄，例如 `/home/agent/projects/my-app`
- 不要在 `/home/agent/projects` 以外的地方建立或修改檔案
- 這個目錄會與本地電腦同步，所以你在這裡寫的程式碼，團隊成員都看得到
- 使用 `git` 進行版本控制，用 `gh` 操作 GitHub（建立 PR、管理 issue 等）
- commit 時不需要設定 git 使用者名稱和信箱，環境已經幫你設定好了
```

### workflow.md（必要）

複製現有角色的 `workflow.md` 即可，內容通用：

```bash
cp agents/bob/.kiro/steering/workflow.md agents/krabs/.kiro/steering/workflow.md
```

### memory.md（會自動被 gitignore）

建立 `agents/krabs/.kiro/steering/memory.md`，初始內容：

```markdown
# 🦀 蟹老闆的記憶

## 團隊成員
（列出其他角色）

## 進行中的專案
（留空）

## 重要決定與約定
（留空）

## 備註
（留空）
```

## 更新 .env

在 `.env` 中新增 token：

```env
DISCORD_BOT_TOKEN_KRABS=你的token
```

注意：`GH_TOKEN` 是所有角色共用的，不需要為每個角色新增。

## 更新 docker-compose.yml（本地開發用）

在 `services` 區塊新增：

```yaml
  krabs:
    build: .
    container_name: krabs
    restart: unless-stopped
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN_KRABS}
      - CHANNEL_GENERAL=${CHANNEL_GENERAL}
      - GIT_AUTHOR_NAME=蟹老闆 (Mr. Krabs)
      - GIT_COMMITTER_NAME=蟹老闆 (Mr. Krabs)
      - GIT_AUTHOR_EMAIL=${GIT_EMAIL}
      - GIT_COMMITTER_EMAIL=${GIT_EMAIL}
      - GH_TOKEN=${GH_TOKEN}
    volumes:
      - ./agents/krabs/config.toml:/etc/openab/config.toml:ro
      - ./agents/krabs:/home/agent
```

需要的環境變數都要列在 `environment` 裡，確保 config.toml 中的 `${VAR}` 都有對應。

**重要：** 如果 agent 的 shell session 需要使用某個環境變數（如 `GH_TOKEN`），
必須在 `config.toml` 的 `[agent]` 區塊的 `inherit_env` 列表中明確列出。
kiro-cli 2.2.0+ 不會自動繼承容器環境變數，只有 `inherit_env` 中列出的才會傳入。

標準 `inherit_env` 配置：
- 所有角色：`["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]`
- 需要 AWS 的角色：額外加上 `"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"`

---

## ECS Fargate Spot 部署（正式環境）

本地 docker-compose 用於開發測試，正式環境部署到 ECS Fargate Spot。

### 1. 建立 Fargate config

建立 `infra/configs/krabs.toml`：

```toml
[discord]
bot_token = "${DISCORD_BOT_TOKEN}"
allowed_channels = ["${CHANNEL_GENERAL}"]
allow_bot_messages = "mentions"
allow_user_messages = "multibot-mentions"

[agent]
command = "kiro-cli"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent/projects"
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]

[pool]
max_sessions = 3
session_ttl_hours = 1

[reactions]
enabled = true
remove_after_reply = false

[reactions.emojis]
queued = "👀"
thinking = "🤔"
tool = "🔥"
coding = "🦀"
web = "⚡"
done = "🆗"
error = "😱"
```

> **注意：** Fargate 版本的 `max_sessions` 和 `session_ttl_hours` 建議設小（3 / 1h），因為 512MB 記憶體有限。本地版可以設大。

### 2. 更新 .env 並同步 SSM

`.env` 新增 token 後，重新執行：

```bash
./infra/setup-ssm-params.sh
```

腳本會自動從 `.env` 讀取所有變數並寫入 SSM Parameter Store。

> **注意：** 如果新角色需要新的 SSM parameter（例如新的 bot token），需要在 `infra/setup-ssm-params.sh` 中加一行：
> ```bash
> put "/bikini-bottom/krabs/discord-bot-token" "${DISCORD_BOT_TOKEN_KRABS:-}"
> ```

### 3. 更新 deploy.sh

在 `infra/deploy.sh` 的 `AGENTS` 陣列中加入新角色：

```bash
AGENTS=("bob" "patrick" "puff" "krabs")
```

### 4. 上傳 config 並部署

```bash
# 上傳 config 到 S3
./infra/deploy.sh ecr

# 部署新角色
./infra/deploy.sh krabs
```

### 5. 首次認證

```bash
./infra/login-agent.sh krabs
```

### 6. 驗證

```bash
# 看 log
aws logs tail /ecs/bikini-bottom --log-stream-name-prefix krabs --follow --region us-east-1

# 在 Discord @蟹老闆 測試
```

### 7. 規格調整（如果 OOM）

```bash
# 升到 1GB memory
./infra/scale-agent.sh krabs 256 1024
```

詳見 [fargate-scaling-sop.md](./fargate-scaling-sop.md)。

---

## 啟動（本地）

```bash
docker compose up -d --build
```

## 首次登入（本地）

```bash
# kiro-cli 登入
docker exec -it krabs kiro-cli login --use-device-flow

# 重啟讓登入生效
docker compose restart krabs
```

注意：`gh` 認證透過 `GH_TOKEN` 環境變數自動完成，不需要手動登入。
環境變數傳遞由 config.toml 的 `inherit_env` 設定控制，確保列出所有需要的變數。

## 驗證

```bash
# 檢查 logs（本地）
docker compose logs krabs --tail 20

# 在 Discord 頻道 @蟹老闆 測試
```

## 檢查清單

### Discord 設定
- [ ] Discord Application 已建立
- [ ] Message Content Intent 已開啟
- [ ] Bot 已邀請到 server

### 角色檔案
- [ ] `agents/krabs/config.toml` 已建立
- [ ] `agents/krabs/.kiro/steering/personality.md` 已建立
- [ ] `agents/krabs/.kiro/steering/workflow.md` 已建立
- [ ] `agents/krabs/.kiro/steering/memory.md` 已建立

### 本地部署
- [ ] `.env` 已新增 `DISCORD_BOT_TOKEN_KRABS`
- [ ] `docker-compose.yml` 已新增 service
- [ ] `kiro-cli login` 已完成
- [ ] Discord 測試 `@` 有回應

### Fargate 部署
- [ ] `infra/configs/krabs.toml` 已建立
- [ ] `infra/setup-ssm-params.sh` 已新增 token parameter
- [ ] `infra/deploy.sh` 的 `AGENTS` 陣列已更新
- [ ] `./infra/setup-ssm-params.sh` 已執行
- [ ] `./infra/deploy.sh krabs` 已執行
- [ ] `./infra/login-agent.sh krabs` 已完成首次認證
- [ ] Discord 測試 `@` 有回應
