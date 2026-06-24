# K3s hostPath 遷移報告

> 日期：2024-06-04
> 狀態：bob 已完成，其餘角色待處理

---

## 目標

將 K3s deployment 的 hostPath 從 `/opt/bikini-bottom/`（獨立 copy）改為直接讀取 repo 目錄 `/home/kdprogramer/Projects/bikini-bottom/`，等同 docker-compose 的 bind mount 行為。改完後不再需要維護兩份資料。

---

## 完成項目

- [x] bob deployment hostPath 改為 repo 路徑
- [x] bob 資料從 `/opt` 完整同步至 repo
- [x] bob 測試通過，Discord 回應正常

---

## 踩坑紀錄

### 1. envFrom 缺失
- **現象：** `all discord.allowed_channels entries failed to parse`，容器 crash
- **原因：** git 裡的 bob.yaml 缺少 `envFrom: configMapRef: channel-ids`，但之前跑的版本有
- **修正：** 加上 envFrom

### 2. subPath 不該存在
- **現象：** `failed to prepare subPath for volumeMount "config"`，CreateContainerConfigError
- **原因：** git 裡的 bob.yaml 有 `subPath: config.toml`，但 config volume 已經是 `type: File` 直接指向 config.toml，不需要 subPath
- **修正：** 移除 subPath

### 3. 目錄權限不足
- **現象：** entrypoint 執行 `ln -sf` 建 steering symlink 時 Permission denied
- **原因：** repo 目錄權限為 `drwxrwxr-x`（775），容器內 agent user 無寫入權限。`/opt` 版本是 `drwxrwxrwx`（777）
- **修正：** `find agents/bob -type d -exec chmod 777 {} \;`

### 4. kiro-cli initialize timeout（根因）
- **現象：** openab spawn kiro-cli 後 30 秒 timeout，Discord 不回應
- **原因：** repo 缺少 kiro-cli 運行時產生的檔案，導致 kiro-cli 無法啟動 ACP session
- **修正：** `rsync -av /opt/bikini-bottom/agents/bob/ → repo/agents/bob/`

---

## 必須從 /opt 同步的關鍵檔案

以下檔案是 kiro-cli 運行時自動產生的，repo 原本沒有：

| 路徑 | 用途 |
|------|------|
| `.local/share/kiro-cli/data.sqlite3` | kiro-cli 本地資料庫（session 索引、狀態） |
| `.local/share/kiro-cli/knowledge_bases/kiro_default/models/` | knowledge base embedding 模型快取 |
| `.semantic_search/models/all-MiniLM-L6-v2/model.safetensors` | 語意搜尋 embedding 模型權重 |
| `.semantic_search/models/all-MiniLM-L6-v2/tokenizer.json` | tokenizer 設定 |

**沒有這些檔案，kiro-cli 無法完成 ACP initialize，會 timeout。**

---

## 其餘角色遷移 SOP

對每個角色依序執行：

```bash
# 1. 完整同步 /opt 資料到 repo
rsync -av --delete /opt/bikini-bottom/agents/<角色>/ /home/kdprogramer/Projects/bikini-bottom/agents/<角色>/

# 2. 修正 .local 權限（如果 rsync 報 permission denied）
sudo rsync -av /opt/bikini-bottom/agents/<角色>/.local/ /home/kdprogramer/Projects/bikini-bottom/agents/<角色>/.local/
sudo chmod -R 777 /home/kdprogramer/Projects/bikini-bottom/agents/<角色>/.local/

# 3. 修正所有目錄權限為 777
find /home/kdprogramer/Projects/bikini-bottom/agents/<角色> -type d -exec chmod 777 {} \;

# 4. Apply deployment（YAML 已改好路徑）
kubectl apply -f k3s/deployments/<角色>.yaml

# 5. 等待 rollout
kubectl rollout status deployment/<角色> -n bikini-bottom --timeout=60s

# 6. 檢查 log 無 error
kubectl logs deployment/<角色> -n bikini-bottom | grep -E "(ERROR|Permission denied)"

# 7. Discord 測試回應
```

---

## 額外踩坑：thread_map 被覆蓋

### 問題
遷移過程中舊容器仍在運行，持續寫入 thread_map。rsync 抓到的是被覆蓋後的版本，導致部分 thread 指向了錯誤的（較新、較小的）session，agent 就像「失憶」一樣。

### 修正方式
1. 用 grep 找出 thread ID 對應的所有 session 檔案
2. 比對大小和首則對話內容，找出最完整的 session
3. 手動修正 thread_map 指向正確 session
4. **必須寫到 host 檔案上**（不是 exec 進容器寫），否則重啟時 entrypoint 合併邏輯會覆蓋

### 教訓
- 遷移時應先停掉舊容器（`kubectl scale --replicas=0`），再 rsync，避免 race condition
- thread_map 是最容易被污染的檔案，遷移後要驗證

---

## 完成狀態

- [x] 所有 agent deployment hostPath 改為 repo 路徑
- [x] 所有 agent 資料完整同步（rsync + sudo .local）
- [x] 目錄權限修正為 777
- [x] thread_map 驗證及修正（bob、squidward、sandy）
- [x] Discord 連線及回應測試通過
- [ ] 刪除 `/opt/bikini-bottom`（全部穩定運行一段時間後再刪）
- [ ] `.gitignore` 加入 `.local/`、`.semantic_search/` 避免大檔案進 git
