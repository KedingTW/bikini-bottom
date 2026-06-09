# 角色狀態備份計畫

> 日期：2026-06-09
> 分支：feat/agent-backup

---

## 一、角色狀態組成

每個 agent 容器的 home 目錄 (`/home/agent`) 對應到 host 的 `agents/<name>/`。
以下是各類狀態的分類：

### 必備份（遺失 = 功能中斷）

| 檔案 | 用途 | 目前保護 |
|------|------|----------|
| `.openab/thread_map.json` | Discord thread ↔ session 映射 | entrypoint 有 backup/merge，但 host 檔案無備份 |
| `.openab/cronjob.toml` | 排程任務定義 | 只有 mermaid-man 的在 git |
| `.local/share/kiro-cli/data.sqlite3` | kiro session 索引 | 無 |
| `.kiro/steering/memory.md` | agent 動態記憶 | .gitignore 排除 |

### 建議備份（可重建但耗時 5-10 分鐘）

| 檔案 | 用途 |
|------|------|
| `.local/share/kiro-cli/knowledge_bases/` | KB embedding 快取 |

### 不需備份（自動重建）

| 檔案 | 說明 |
|------|------|
| `.semantic_search/models/` | 首次啟動自動下載（~90MB） |
| `projects/` | 已 symlink 到 NAS，且可 git clone |
| `.cache/`, `.conda/`, `node-v*/` | runtime 快取 |

---

## 二、現有保護機制（已有）

1. **Git 版控**：config.toml、自訂 steering、avatar
2. **entrypoint-wrapper.sh**：容器啟動時 backup/merge thread_map.json
3. **NAS symlink**：projects 目錄指向 NAS（`/nas/agents/<name>/projects`）
4. **pack-kiro-runtime.sh**：打包 kiro runtime 供新角色使用

### 缺口

- thread_map.json 只在容器**重啟時**保護，host 檔案損壞無法恢復
- cronjob.toml 大部分未進 git
- data.sqlite3 完全無備份
- memory.md 完全無備份
- 無定時自動備份機制

---

## 三、備份方案設計

### 架構

```
Host cron (每日 03:00)
    │
    ▼
scripts/backup-agents.sh
    │
    ├── 1. SQLite safe copy（避免寫入中損壞）
    ├── 2. 關鍵檔案 rsync 到 NAS 備份區
    ├── 3. 壓縮為日期命名 tar.gz
    └── 4. 清理 > 7 天的舊備份

NAS 備份目錄：
/nas/backups/agents/
├── bob/
│   ├── 20260609.tar.gz
│   ├── 20260608.tar.gz
│   └── ...（保留 7 天）
├── patrick/
└── ...
```

### 備份內容清單

每個角色打包以下路徑：

```
.openab/thread_map.json
.openab/cronjob.toml
.local/share/kiro-cli/data.sqlite3
.local/share/kiro-cli/data.sqlite3-wal    （如果存在）
.local/share/kiro-cli/data.sqlite3-shm    （如果存在）
.kiro/steering/memory.md
```

### 為什麼不用 Docker volume backup？

- agents 目錄是 bind mount 而非 named volume
- 直接操作 host 檔案系統更簡單可靠
- 不需停止容器（只要處理好 SQLite）

---

## 四、實作

### 4.1 備份腳本：`scripts/backup-agents.sh`

（見同 PR 提交的檔案）

### 4.2 .gitignore 調整

將 `.openab/cronjob.toml` 納入 Git 追蹤（目前被 `agents/*/.openab/` 整包排除）：

```diff
- # OpenAB runtime 資料（thread_map、session 等）
- agents/*/.openab/
+ # OpenAB runtime — 只排除動態檔案
+ agents/*/.openab/thread_map.json
+ agents/*/.openab/thread_map.json.bak
+ agents/*/.openab/sessions/
+ agents/*/.openab/*.log
```

這樣 `cronjob.toml` 會自動被 git 追蹤，提供版本歷史。

### 4.3 NAS 備份目錄初始化

在 `scripts/init-nas-dirs.bat` 加入：

```bat
mkdir "%NAS_BASE%\backups\agents\bob"
mkdir "%NAS_BASE%\backups\agents\patrick"
...（每個角色）
```

### 4.4 Host crontab

```cron
# 每日 03:00 備份角色狀態到 NAS
0 3 * * * /home/kdprogramer/Projects/bikini-bottom/scripts/backup-agents.sh >> /var/log/agent-backup.log 2>&1
```

---

## 五、還原 SOP

### 情境 A：單一角色 thread_map 遺失

```bash
# 1. 找到最近備份
LATEST=$(ls -1t /nas/backups/agents/bob/*.tar.gz | head -1)

# 2. 解壓 thread_map
tar -xzf "$LATEST" -C /tmp/restore .openab/thread_map.json

# 3. 覆蓋
cp /tmp/restore/.openab/thread_map.json agents/bob/.openab/

# 4. 重啟容器（entrypoint 會 merge）
docker compose restart bob
```

### 情境 B：角色完全重建

```bash
# 1. 從 git 取得 config + steering
git checkout master -- agents/bob/

# 2. 從備份還原 runtime 狀態
LATEST=$(ls -1t /nas/backups/agents/bob/*.tar.gz | head -1)
tar -xzf "$LATEST" -C agents/bob/

# 3. 從 pack-kiro-runtime 還原模型檔（如果 .local 也遺失）
tar -xzf kiro-runtime-files.tar.gz -C agents/bob/

# 4. 修正權限
find agents/bob -type d -exec chmod 777 {} \;

# 5. 啟動
docker compose up -d bob
```

### 情境 C：整機災難恢復

```bash
# 1. Clone repo（含 config + steering）
git clone <repo-url> bikini-bottom && cd bikini-bottom
cp /nas/backups/.env.gpg . && gpg -d .env.gpg > .env

# 2. 還原所有角色
for agent in bob patrick puff squidward sandy pearl larry mermaid-man conch; do
    LATEST=$(ls -1t /nas/backups/agents/$agent/*.tar.gz | head -1)
    mkdir -p agents/$agent/.openab agents/$agent/.local
    tar -xzf "$LATEST" -C agents/$agent/
done

# 3. 還原 kiro runtime 模型
tar -xzf /nas/backups/kiro-runtime-files.tar.gz -C agents/bob/
# 複製到其他角色...

# 4. 修正權限 + 啟動
find agents -type d -exec chmod 777 {} \;
docker compose up -d --build
```

---

## 六、監控

### 備份健康檢查（可由 conch cronjob 每日 09:00 執行）

```bash
#!/bin/bash
BACKUP_BASE="/nas/backups/agents"
TODAY=$(date +%Y%m%d)
MISSING=()

for agent in bob patrick puff squidward sandy pearl larry mermaid-man conch; do
    if [ ! -f "$BACKUP_BASE/$agent/$TODAY.tar.gz" ]; then
        MISSING+=("$agent")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "⚠️ 備份缺失: ${MISSING[*]}"
    exit 1
fi
echo "✅ 所有角色今日備份完成"
```

---

## 七、執行計畫

| # | 動作 | 優先級 | 預估時間 |
|---|------|--------|----------|
| 1 | 修改 .gitignore 追蹤 cronjob.toml | 高 | 5 分鐘 |
| 2 | 提交各角色 cronjob.toml 到 git | 高 | 10 分鐘 |
| 3 | 建立 scripts/backup-agents.sh | 高 | 15 分鐘 |
| 4 | NAS 建立 backups 目錄 | 中 | 5 分鐘 |
| 5 | 設定 host crontab | 中 | 5 分鐘 |
| 6 | 加密備份 .env 到 NAS | 中 | 10 分鐘 |
| 7 | 加入備份健康檢查到 conch cronjob | 低 | 15 分鐘 |

---

## 八、注意事項

- **SQLite 安全拷貝**：data.sqlite3 在容器運行中可能被寫入，使用 `sqlite3 .backup` 或在凌晨備份（通常無人使用）降低風險
- **.env 備份**：包含所有 API key/token，必須加密（`gpg -c`）後才存到 NAS
- **NAS 斷線**：備份腳本應有 fallback，NAS 不可用時暫存到本機 `/opt/backups/`
- **備份大小**：每個角色預估 5-20MB（主要是 data.sqlite3），10 個角色 × 7 天 ≈ 1.4GB
