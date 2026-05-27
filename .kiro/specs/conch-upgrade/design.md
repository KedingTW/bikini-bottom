# 神奇海螺升級 — 設計

## 架構變更

### Before

```
services/magic-conch/  (Python bot, CONCH token)
  → slash command: /conch-status, /conch-heal, /conch-logs, /conch-archive
  → docker.sock 掛載

services/slash-bot/  (Python bot, GARY token)
  → slash command: /usage, /activity
```

### After

```
agents/conch/  (OpenAB agent, CONCH token)
  → AI 對話，被 mention 時回答
  → 不掛 docker.sock，不管容器

services/slash-bot/  (Python bot, GARY token)
  → slash command: /usage, /activity（原有）
  → slash command: /status, /heal, /logs, /archive（從海螺搬來）
  → docker.sock 掛載（新增）
  → openai 依賴（新增，用於 /archive 摘要）
```

## 小蝸 (slash-bot) 改動

### 依賴新增

```
docker==7.1.0
openai==1.82.0
```

### docker-compose 改動

- `slash-bot` service 新增 volume: `/var/run/docker.sock:/var/run/docker.sock:ro`
- `slash-bot` service 新增 env: `CONCH_ADMIN_IDS`, `CONCH_OPERATOR_ROLE_IDS`, `OPENAI_API_KEY`
- 移除 `magic-conch` service

### 程式碼

- 將 `services/magic-conch/bot.py` 中的指令邏輯搬到 `services/slash-bot/bot.py`
- 指令改名：`/conch-status` → `/status`，`/conch-heal` → `/heal`，`/conch-logs` → `/logs`，`/conch-archive` → `/archive`
- 移除頻道限制（或改為小蝸的頻道）
- `ROLE_MAP` 和 `MANAGED_CONTAINERS` 更新（加入 pearl、larry、conch）

## 神奇海螺 (agents/conch/) OpenAB Agent

### 目錄結構

```
agents/conch/
├── config.toml
├── .gitconfig
├── .config/gh/hosts.yml
├── .kiro/
│   ├── steering/
│   │   ├── personality.md
│   │   └── workflow.md
│   └── settings/
│       └── mcp.json
└── .openab/
    ├── cronjob.toml
    └── thread_map.json
```

### config.toml 重點

- `allowed_channels`：蟹堡王論壇、會議室論壇、廣場、實驗室、電視台、急診室
- `allow_bot_messages = "mentions"` — bot 也能問海螺
- `allowed_role_ids`：比奇堡小夥伴們（讓群組 mention 也觸發）
- 不需要 `GH_TOKEN`、`AWS_*`（海螺不碰 git 和 AWS）
- 不需要 `AGENT_SKILLS`（海螺不產文件）

### personality.md 設計

卡通原版風格：
- 「噢～全能的神奇海螺啊～我們該怎麼辦？」
- 回答簡短：「什麼都不做。」「不行。」「試試看吧。」「再問一次。」
- 但在真正有用的問題上，會給出精準方向

### workflow.md 設計

- 不維護 `_projects.md`、`_status.md`
- 不走 git flow
- 不開 PR
- 收到問題 → 簡短回答
- 如果問題涉及流程 → 指引該找誰
- 如果問題太模糊 → 拒絕回答或要求重新提問

### docker-compose

```yaml
conch:
  build: .
  container_name: conch
  restart: unless-stopped
  <<: *extra-hosts
  env_file: .env
  environment:
    - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN_CONCH}
    - KIRO_API_KEY=${KIRO_API_KEY_CONCH}
    - GIT_AUTHOR_NAME=神奇海螺 (Magic Conch)
    - GIT_COMMITTER_NAME=神奇海螺 (Magic Conch)
    - GIT_AUTHOR_EMAIL=${GIT_EMAIL}
    - GIT_COMMITTER_EMAIL=${GIT_EMAIL}
    - AGENT_NAME=conch
  volumes:
    - ./agents/conch/config.toml:/etc/openab/config.toml:ro
    - ./agents/conch:/home/agent
    - nas:/nas
    - ./shared/steering:/opt/steering:ro
    - ./shared/skills:/opt/skills:ro
```

## NAS

建立 `Z:\...\88.BikiniBottom\agents\conch\projects`

## 更新清單

| 檔案 | 改動 |
|------|------|
| `docker-compose.yml` | 移除 magic-conch，新增 conch，修改 slash-bot |
| `services/slash-bot/bot.py` | 合併容器管理指令 |
| `services/slash-bot/requirements.txt` | 加 docker、openai |
| `services/slash-bot/Dockerfile` | 可能不用改（pip install 會裝新依賴） |
| `agents/conch/` | 全新建立 |
| `shared/steering/team-members.md` | 更新海螺的描述 |
| `README.md` | 更新角色表 |
| `docs/bot-setup-sop.md` | 更新容器對應表 |
| `services/magic-conch/bot.py` | 保留但標記為 deprecated（或直接刪除） |
