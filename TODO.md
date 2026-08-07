# TODO（2026-06-25 晚間遷移後）

## 高優先

### 1. 修正備份策略
- **分支**：`fix/backup-strategy`
- 備份腳本已改成整目錄備份，但需驗證：
  - 確認所有角色（含 keding-dc）每小時備份正確跑完
  - 確認 `.openab/thread_map.json` 和 `data.sqlite3` 都有被包進 tar
  - 考慮加入 keding-wecom 的備份
  - restore 腳本 (`scripts/restore-agent.sh`) 也需要更新路徑

### 2. 遺漏檢查
- **分支**：`fix/remaining-cleanup`
- `scripts/k3s-setup.sh` — 還有 NAS 字眼
- `scripts/restore-agent.sh` — 還有 NAS 路徑
- `docs/` 底下多份文件有 NAS 字眼（agent-backup-plan.md、k3s-migration-plan.md、k3s-operations-guide.md、new-agent-sop.md、bot-setup-sop.md）
- `.kiro/steering/k3s-migration.md` — 有 NAS 字眼
- `.kiro/specs/conch-upgrade/design.md` — 有 NAS 字眼
- `k3s/volumes/nas-pv.yaml` — 整個檔案用舊名
- `k3s/kustomization.yaml` — 可能引用 nas-pv

## 中優先

### 3. Image 更新問題
- K3s 沒有載入新的 bikini-bottom image（entrypoint 的 groupadd/usermod 改動未生效）
- 需要 `sudo crictl rmi <舊image-id>` 或改 image tag 強制拉取
- 目前用 chmod 777 context/ 暫時繞過

### 4. 章魚哥家目錄清理
- 家目錄裡有舊 repo（als-api、als-vue、hr-backend、mes-backend）佔用本地空間
- 需要 sudo 權限刪除（部分檔案 owner 不是 kdprogramer）
- 不急，等有空再清

### 5. keding-dc entrypoint 的 image 也未更新
- `Dockerfile.keding-dc` 改了但 K3s 裡的 pod 還是用舊 image
- 下次重啟時會自動用新的（如果 image tag 沒變的話也有 cache 問題）
- 需要驗證

## 低優先

### 6. `_archived_duplicates` 目錄
- `agents/_archived_duplicates/` 裡的舊角色資料可以考慮搬到 kd-dev 備份後刪除

### 7. shared-drive.md 裡的 `/shared/drop/` 和 `/shared/docs/`
- 海綿盤點時有角色說這些目錄不存在
- 需確認 kd-dev 上是否有 `shared/drop/` 和 `shared/docs/`，沒有就建

### 8. gary 的 thread_map.json 丟失
- 已建空的 `{}`，舊的 mapping 無法恢復
- 小蝸在舊 thread 回覆一次後會自動重建 mapping
