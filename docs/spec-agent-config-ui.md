# 開發規格：Admin UI — Agent Config 動態管理

> 版本：v1.0  
> 日期：2026-06-11  
> 狀態：待實作

## 目標

讓管理者可以透過 Admin UI 直接編輯 agent 的 `config.toml`（特別是 `trusted_bot_ids`、`allowed_channels`、`allowed_role_ids` 等），並支援新增角色時自動產生 config。解決每次新增角色都需要手動改多個檔案且容易遺漏的問題。

## 現況分析

### 現有架構
- Admin UI 前端：Vue 3 + Tailwind，部署於 k3s `admin` deployment
- Admin 後端：FastAPI（Python），提供 REST API
- Agent config：各 `agents/<alias>/config.toml`，透過 k3s hostPath 掛載到容器
- 已有 `/api/agents/{name}/config` GET/PUT API（讀寫原始 TOML 文字）
- 已有 `AgentConfig.vue` 頁面（卡片模式唯讀 + TOML raw 編輯器）

### 痛點
1. 新增角色時需手動更新所有既有 agent 的 `trusted_bot_ids`（10+ 個檔案）
2. 容易遺漏導致 bot-to-bot mention 失敗
3. 修改需 SSH 到伺服器手動編輯，無法從 UI 操作
4. 沒有驗證機制，格式錯誤會導致 OpenAB 啟動失敗

## 功能規格

### Phase 1：Bot 互信管理面板

#### 頁面位置
在「AI 角色管理」下新增「🔗 Bot 互信」選單項目。

#### UI 設計
- **矩陣表格**：橫軸和縱軸都是所有 bot，交叉點顯示 ✓（已信任）或 ✗（未信任）
- 對角線灰色（自己不能信任自己）
- 點擊 ✗ 可加入信任，點擊 ✓ 可移除
- 頂部操作列：
  - 「全部互信」按鈕：一鍵讓所有 bot 互相信任
  - 「儲存」按鈕：寫入所有變更的 config.toml
  - 「儲存並重啟」按鈕：寫入後自動重啟受影響的 agent

#### API 設計

```
GET /api/trust-matrix
Response: {
  "bots": [
    {"name": "bob", "display": "海綿寶寶", "uid": "1492085509596516362"},
    {"name": "sandy", "display": "珊迪", "uid": "1504275756488986774"},
    ...
  ],
  "matrix": {
    "bob": ["1496023645083009024", "1509104920954142871", ...],
    "sandy": ["1492085509596516362", ...],
    ...
  }
}

PUT /api/trust-matrix
Body: {
  "matrix": {
    "bob": ["uid1", "uid2", ...],
    "sandy": ["uid1", "uid2", ...],
    ...
  },
  "restart": true  // 是否自動重啟
}
Response: { "ok": true, "updated": ["bob", "sandy", ...], "restarted": [...] }
```

#### 後端邏輯
1. GET：讀取所有 agent 的 config.toml，解析 `trusted_bot_ids`
2. PUT：使用 `tomlkit` 解析每個 config.toml，只修改 `trusted_bot_ids` 值，保留格式和註解
3. 寫入後若 `restart=true`，呼叫 k8s API rollout restart

---

### Phase 2：Config 結構化編輯

#### 將 AgentConfig.vue 的卡片模式改為可編輯表單

| 區塊 | 欄位 | 輸入類型 |
|------|------|---------|
| Discord | `allow_bot_messages` | 下拉選單（off / mentions / all） |
| Discord | `allow_user_messages` | 下拉選單（involved / mentions / multibot-mentions） |
| Discord | `max_bot_turns` | 數字輸入 |
| Discord | `trusted_bot_ids` | 多選列表（從 bot registry 選取） |
| Discord | `allowed_channels` | 多選列表（顯示 channel 名稱） |
| Discord | `allowed_role_ids` | 列表（可新增/刪除） |
| Pool | `max_sessions` | 數字輸入 |
| Pool | `session_ttl_hours` | 數字輸入 |
| Reactions | `enabled` | Toggle 開關 |
| Reactions | emojis | Emoji 選擇器 |

#### API 設計

```
PATCH /api/agents/{name}/config
Body: {
  "discord": {
    "allow_bot_messages": "mentions",
    "trusted_bot_ids": ["id1", "id2"]
  },
  "pool": {
    "max_sessions": 15
  }
}
Response: { "ok": true }
```

後端使用 `tomlkit` 做 partial update，只修改傳入的欄位。

---

### Phase 3：新增角色全流程

#### UI 入口
角色配置頁面右上角「+ 新增角色」按鈕，開啟多步驟對話框。

#### 步驟

**Step 1：基本資訊**
- 別名（英文小寫，用於目錄名）
- 中文名稱
- Emoji 圖標
- 職責描述
- Bot Token（輸入後自動解碼出 UID）

**Step 2：頻道與權限**
- 選擇允許的 Discord 頻道（多選，從現有頻道列表選）
- 選擇觸發 role（多選）
- `allow_bot_messages` 模式選擇
- `allow_user_messages` 模式選擇

**Step 3：互信設定**
- 預設勾選「信任所有現有 bot」
- 矩陣預覽：新 bot 會出現在列表中

**Step 4：確認與建立**
- 預覽將產生的 config.toml
- 顯示將更新的其他 agent 清單
- 「建立」按鈕

#### 後端自動化流程

```
POST /api/agents
Body: {
  "alias": "karen",
  "display": "乖乖",
  "icon": "🤖",
  "role": "助理",
  "bot_token_env": "DISCORD_BOT_TOKEN_KAREN",
  "allowed_channels": ["${CHANNEL_KRUSTY_KRAB}", ...],
  "allowed_role_ids": ["role1"],
  "trust_all": true
}
```

後端執行：
1. 從 `.env` 讀取 bot token，base64 解碼取得 UID
2. 建立 `agents/<alias>/` 目錄結構
3. 從 template 產生 `config.toml`
4. 建立 `.kiro/steering/personality.md` 骨架
5. 建立 `.openab/cronjob.toml`（空）
6. 將新 bot UID 加入所有既有 agent 的 `trusted_bot_ids`
7. 更新 `shared/steering/team-members.md`（追加一行）
8. 產生 k3s deployment YAML（從 template）
9. 執行 `kubectl apply -f` 建立 deployment
10. 重啟所有既有 agent（讓 trusted_bot_ids 生效）

---

## 技術規格

### 後端依賴新增
- `tomlkit`：TOML 解析/寫入，保留格式和註解（不像 `tomli` 會重排）

### Config Template

位置：`services/admin/templates/agent-config.toml.tmpl`

```toml
[discord]
bot_token = "${DISCORD_BOT_TOKEN}"
allowed_channels = [{{channels}}]
allow_bot_messages = "mentions"
trusted_bot_ids = [{{trusted_ids}}]
allow_user_messages = "mentions"
allowed_role_ids = [{{role_ids}}]
max_bot_turns = 100

[agent]
command = "kiro-cli"
args = ["acp", "--trust-all-tools"]
working_dir = "/home/agent/projects"
env = { KIRO_API_KEY = "${KIRO_API_KEY}" }
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "KIRO_API_KEY"]

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
coding = "📋"
web = "⚡"
done = "🆗"
error = "😱"

[reactions.timing]
debounce_ms = 700
stall_soft_ms = 10000
stall_hard_ms = 30000
done_hold_ms = 1500
error_hold_ms = 2500

[cron]
usercron_enabled = true
usercron_path = "cronjob.toml"
```

### Bot Registry

位置：`services/admin/data/bot-registry.json`（或直接從各 config.toml 動態解析）

```json
{
  "bob": {"uid": "1492085509596516362", "display": "海綿寶寶", "icon": "🧽"},
  "patrick": {"uid": "1496023645083009024", "display": "派大星", "icon": "⭐"},
  ...
}
```

### 驗證規則

寫入 config.toml 前驗證：
1. `trusted_bot_ids` 不能包含自己的 UID
2. `allowed_channels` 不能為空（除非 `allow_all_channels = true`）
3. UID 格式必須是 17-20 位數字
4. TOML 語法正確性

### 安全考量
- Config 修改需登入且為 admin 角色
- 修改動作記錄到操作日誌（`deploy_history` 表）
- Bot Token 永遠不透過 API 回傳，只顯示環境變數名
- 重啟操作有 rate limit（每個 agent 至少間隔 30 秒）

---

## 實作順序

| 階段 | 內容 | 預估工時 |
|------|------|---------|
| Phase 1 | Bot 互信管理面板 | 2-3 天 |
| Phase 2 | Config 結構化編輯（卡片模式可寫） | 3-4 天 |
| Phase 3 | 新增角色全流程 | 4-5 天 |

建議先做 Phase 1，因為這是目前最痛的點且範圍最小。

---

## 參考

- OpenAB config-reference：`refs/openab/docs/config-reference.md`
- OpenAB multi-agent：`refs/openab/docs/multi-agent.md`
- 現有 admin 後端：`services/admin/backend/app.py`
- 現有 admin 前端：`services/admin/frontend/src/views/AgentConfig.vue`
- Bot UID 對照：`.kiro/steering/agent-registry.md`
