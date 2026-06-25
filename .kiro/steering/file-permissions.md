# Agent 檔案與掛載配置規範

## ⚠️ 操作紀律（必讀）

1. **絕對不刪除任何檔案** — 除非明確得到人類確認
2. **先測試一個角色** — 確認 OK 才套用其他角色
3. **不重啟正在工作的角色** — 重啟需跟人類確認
4. **修改前先備份** — 特別是 `.openab/` 和 `data.sqlite3`
5. **不要用 sleep 等待** — 浪費時間，直接檢查狀態

---

## 環境資訊

| 項目 | 值 |
|------|-----|
| 容器 agent user | uid=1000, gid=1000 |
| Host 檔案 owner | kdprogramer, uid=1002, gid=1002 |
| K8s Pod securityContext | `supplementalGroups: [1002]` |
| 效果 | agent 容器啟動時附加 gid=1002，可寫 group=1002 的檔案 |

---

## Volume 掛載配置（比奇堡）

以 gary 為例，所有比奇堡角色結構相同：

| Volume Name | Host Path | 容器內 | 讀寫 |
|-------------|-----------|--------|------|
| config | 本地 `agents/bikini-bottom/<name>/config.toml` | `/etc/openab/config.toml` | readOnly |
| home | 本地 `agents/bikini-bottom/<name>` | `/home/agent` | rw |
| workspace | `/mnt/kd-dev/agents/<name>` | `/home/agent/workspace` | rw |
| shared-workspace | `/mnt/kd-dev/shared/workspace` | `/shared/workspace` | rw |
| shared-steering | `/mnt/kd-dev/shared/steering` | `/opt/steering` | readOnly |
| shared-skills | `/mnt/kd-dev/shared/skills` | `/opt/skills` | readOnly |

### 路徑說明

- **本地** = `/home/kdprogramer/Projects/bikini-bottom/`（本機 SSD，git 管理）
- **/mnt/kd-dev** = `88.BikiniBottom`（CIFS 共用儲存）
- 家目錄（/home/agent）存系統設定：.kiro、.openab、config.toml
- 工作區（/home/agent/workspace）存工作檔案：projects 等
- config.toml 的 `working_dir = "/home/agent/workspace"`

---

## 角色目錄結構（本地）

```
agents/bikini-bottom/<name>/
├── config.toml           ← OpenAB 核心設定（readOnly mount 到 /etc/openab/）
├── avatar.png
├── .kiro/
│   ├── steering/         ← personality.md, workflow.md, memory.md
│   ├── context/          ← 觸發式上下文（agent 可寫）
│   ├── settings/         ← mcp.json, cli.json
│   └── skills/           ← symlink 到 /opt/skills
├── .openab/
│   ├── thread_map.json   ← Discord thread 對應表（重要！不可遺失）
│   └── cronjob.toml      ← 排程任務
├── .local/share/kiro-cli/
│   └── data.sqlite3      ← 對話歷史 DB（重要！）
└── .gitconfig
```

---

## 權限矩陣

### Agent 可寫入的檔案

| 檔案 | 誰寫 | 權限 |
|------|------|------|
| memory.md | Agent | `0664` |
| cronjob.toml | Agent | `0664` |
| context/*.md | Agent | 目錄 `0775`，檔案 `0664` |
| thread_map.json | 框架 | `0664` |
| cli.json | 框架 | `0664` |
| data.sqlite3 | 框架 | `0664` |
| ~/workspace/ 底下所有 | Agent | kd-dev CIFS（0777） |

### Agent 唯讀的檔案

| 檔案 | 掛載方式 |
|------|----------|
| config.toml | readOnly mount |
| personality.md | 家目錄內 |
| workflow.md | 家目錄內 |
| mcp.json | 家目錄內 |
| /opt/steering/* | readOnly mount |
| /opt/skills/* | readOnly mount |

---

## 備份機制

- 腳本：`scripts/backup-agents.sh`
- 排程：host crontab 每小時執行
- 目標：`/mnt/kd-dev/backups/agents/<group>/<name>/`
- 備份整個本地角色目錄（排除 .local/lib、node_modules、miniconda 等大型目錄）
- SQLite 用安全拷貝
- full 模式（每日 03:00）包含 semantic_search models

---

## 常見踩雷與避免方式

| 踩雷 | 原因 | 避免方式 |
|------|------|---------|
| 角色失去對話記憶 | thread_map.json 遺失 | 不刪除 .openab/；entrypoint 保留 .bak 不刪 |
| 角色 spawn 失敗 | working_dir 路徑不存在 | 確保 config.toml 的 working_dir 對應容器內有效路徑 |
| shared steering 版本不同步 | 本地和 kd-dev 是兩份 | 修改本地後記得同步到 /mnt/kd-dev/shared/steering/ |
| 新 pod 掛載失敗 | yaml 裡的 hostPath 路徑錯 | apply 前確認路徑存在 |
| team-members.md 編碼損壞 | 歷史問題 | 用 `file` 確認 UTF-8，損壞就重寫 |
| 角色目錄被重複建立 | steering 文件裡寫錯路徑 | 路徑統一用 `agents/bikini-bottom/<alias>/` |

---

## 待辦（未完成）

### context 目錄寫入權限問題
- **症狀**：agent (uid=1000) 無法寫入 `~/.kiro/context/`（775, owner 1002:1002）
- **原因**：K8s supplementalGroups 加了 1002，但 entrypoint 用 `setpriv --init-groups` 降權時從 /etc/group 重算 groups，丟掉了 K8s 注入的 supplemental group
- **修正方式**：entrypoint 裡在 setpriv 前執行 `groupadd -g 1002 kd && usermod -aG kd agent`（已加入 entrypoint.sh 但 image 尚未被 K3s 載入）
- **剩餘步驟**：需要讓 K3s 使用新 image（docker image ID 不同，但 K3s 用了 cache）。可能需要 `kubectl rollout restart` 搭配 `crictl rmi` 或改 image tag 強制拉取
- **影響**：所有角色的 context/ 目前無法寫入，memory.md 和 workspace 不受影響（memory 在 777 的 steering 目錄、workspace 在 CIFS 0777）
