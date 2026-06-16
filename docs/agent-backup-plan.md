# 角色狀態備份與還原計畫

> 更新日期：2026-06-16
> 分支：kiro_20260609_agent-backup

---

## 一、RPO / RTO 目標

| 指標 | 目標 | 說明 |
|------|------|------|
| **RPO** (Recovery Point Objective) | ≤ 1 小時 | 每小時備份一次，最多遺失 1 小時的資料 |
| **RTO** (Recovery Time Objective) | ≤ 5 分鐘（單一角色）/ ≤ 15 分鐘（全體） | 從 NAS 解壓 + 重啟 pod |

---

## 二、備份範圍

### 2.1 角色清單（3 個伺服器群組，15 個角色）

| 群組 | 角色 |
|------|------|
| bikini-bottom | bob, patrick, puff, squidward, sandy, pearl, larry, mermaid-man, conch, gary |
| keding-dc | captain, ironman, strange, order-transform |
| keding-wecom | order-transform |

### 2.2 備份檔案內容

| 路徑 | 重要性 | 遺失影響 |
|------|--------|----------|
| `.openab/thread_map.json` | 🔴 關鍵 | 遺失 = bot 忘記所有對話，無法接續對話 |
| `.openab/cronjob.toml` | 🔴 關鍵 | 遺失 = 排程任務全部消失 |
| `.local/share/kiro-cli/data.sqlite3` (+wal/shm) | 🔴 關鍵 | 遺失 = kiro session 索引消失 |
| `.local/share/kiro-cli/knowledge_bases/` | 🔴 關鍵 | 遺失 = KB embedding 消失，角色知識庫歸零、智商崩壞 |
| `.semantic_search/models/` | 🟡 重要 | 遺失 = 語意搜尋功能暫停，需重新下載 88MB 模型 |
| `.kiro/steering/memory.md` | 🟡 存在才備 | 遺失 = agent 動態記憶消失（目前只有 gary 在用） |

### 2.3 額外備份

| 項目 | 說明 |
|------|------|
| `.env` | 所有 API key/token，GPG 加密後存 NAS |

---

## 三、備份機制

### 3.1 架構

```
Host cron (每小時 + 每日)
    │
    ▼
scripts/backup-agents.sh
    │
    ├── 1. SQLite 安全拷貝（sqlite3 .backup 指令）
    ├── 2. rsync 關鍵檔案到暫存目錄
    ├── 3. tar.gz 壓縮（時間戳命名）
    ├── 4. tar -tzf 驗證完整性
    ├── 5. 存放到 NAS
    ├── 6. .env GPG 加密備份
    └── 7. 清理 > 7 天的舊備份
```

### 3.2 備份位置

```
/mnt/nas/backups/agents/
├── bikini-bottom/
│   ├── bob/
│   │   ├── 20260616_1400.tar.gz         ← 每小時（不含 models）
│   │   ├── 20260616_0300_full.tar.gz    ← 每日完整（含 models）
│   │   └── ...
│   ├── patrick/
│   └── ...
├── keding-dc/
│   ├── captain/
│   └── ...
├── keding-wecom/
│   └── order-transform/
└── env/
    ├── 20260616_1400.env.gpg            ← .env 加密備份
    └── ...
```

### 3.3 排程

```cron
# 每小時 - 輕量備份（不含 semantic_search/models）
0 * * * * /home/kdprogramer/Projects/bikini-bottom/scripts/backup-agents.sh --mode hourly >> /var/log/agent-backup.log 2>&1

# 每日 03:00 - 完整備份（含 models）
0 3 * * * /home/kdprogramer/Projects/bikini-bottom/scripts/backup-agents.sh --mode full >> /var/log/agent-backup-full.log 2>&1
```

### 3.4 保留策略

- 所有備份保留 **7 天**，到期自動刪除
- 空間估算：
  - 每小時備份：15 agent × ~5MB × 24 × 7 ≈ 12.6GB
  - 每日完整：15 agent × 90MB × 7 ≈ 9.5GB
  - 總計：~22GB（NAS 18TB 可用）

### 3.5 執行方式

腳本需要 **sudo** 權限（容器內檔案 owner 為 `twkder`，uid=1000）：

```bash
# 手動執行（測試）
sudo bash scripts/backup-agents.sh --mode hourly

# 完整備份
sudo bash scripts/backup-agents.sh --mode full
```

### 3.6 NAS 斷線 Fallback

若 `/mnt/nas` 不可寫入，自動切換到本機 `/opt/backups/agents/`。
NAS 恢復後下一輪備份自動寫回 NAS。

---

## 四、還原 SOP

### 4.0 還原工具

提供一鍵還原腳本 `scripts/restore-agent.sh`：

```bash
# 查看可用備份
sudo bash scripts/restore-agent.sh --list bob

# 還原單一角色（最新備份）
sudo bash scripts/restore-agent.sh bob

# 還原科定DC角色
sudo bash scripts/restore-agent.sh keding-dc/captain

# 還原指定時間點
sudo bash scripts/restore-agent.sh bob 20260616_1400

# 還原 .env
sudo bash scripts/restore-agent.sh --env

# 災難恢復：全體還原
sudo bash scripts/restore-agent.sh --all
```

### 4.1 情境 A：單一角色 thread_map 或 data.sqlite3 損壞

```bash
sudo bash scripts/restore-agent.sh bob
```

**內部流程：**
1. 找到最新備份 (`/mnt/nas/backups/agents/bikini-bottom/bob/`)
2. 驗證 tar 完整性
3. 解壓到暫存目錄
4. rsync 到 agent 目錄（不刪除其他檔案）
5. 修正檔案權限（chown twkder:twkder）
6. `kubectl rollout restart deployment bob -n bikini-bottom`

**預估 RTO：2~3 分鐘**

### 4.2 情境 B：單一角色完全重建

```bash
# 1. 從 git 確認 config/steering
git checkout master -- agents/bob/config.toml agents/bob/.kiro/steering/

# 2. 還原 runtime（使用 full 備份）
sudo bash scripts/restore-agent.sh bob

# 3. 驗證
kubectl logs deployment/bob -n bikini-bottom --tail=20
```

**預估 RTO：5 分鐘**

### 4.3 情境 C：keding-dc 子角色還原

```bash
sudo bash scripts/restore-agent.sh keding-dc/captain
```

Deployment 名稱自動對應為 `keding-dc-captain`。

### 4.4 情境 D：整機災難恢復

```bash
# 1. Clone repo
git clone https://github.com/KedingTW/bikini-bottom.git
cd bikini-bottom

# 2. 還原 .env
sudo bash scripts/restore-agent.sh --env

# 3. 全體還原
sudo bash scripts/restore-agent.sh --all

# 4. 啟動 k3s 服務
kubectl apply -f k3s/deployments/ --recursive
```

**預估 RTO：10~15 分鐘**

---

## 五、注意事項

### 執行權限

- 備份腳本需要 `sudo`（讀取 twkder 所有的 data.sqlite3）
- crontab 設定在 root 的 crontab（`sudo crontab -e`）

### SQLite 安全

- 使用 `sqlite3 .backup` 指令確保一致性
- 若 sqlite3 指令不可用，fallback 為直接 cp（每小時備份時通常安全）

### .env 安全

- GPG 對稱加密（AES256）
- Passphrase 預設寫在腳本中（`bikini-bottom-backup-2026`）
- 正式環境建議改為從環境變數 `BACKUP_PASSPHRASE` 讀取

### 不中斷服務

- 備份過程不會重啟任何 pod
- 只有還原時才會重啟對應的 pod
- 還原使用 rsync（合併），不會刪除目標目錄中的其他檔案

---

## 六、TODO（後續處理）

- [ ] memory.md 目前只有 gary 在用，其他角色未啟用 → 需研究原因
- [ ] Admin 後台整合備份狀態顯示（最後備份時間、大小、健康狀態）
- [ ] Admin 後台提供一鍵 restore 功能
- [ ] 備份健康通知（失敗時發 Discord 告警）
- [ ] 考慮 BACKUP_PASSPHRASE 改用 K8s Secret 或 AWS SM 管理
