# 踩雷紀錄 — 科定DC Bot

---

## 2026-06-11：kiro-cli connection closed（改權限導致 session 寫入失敗）

### 症狀

```
INFO openab::acp::connection: initialized agent="Kiro CLI Agent" load_session=true
ERROR openab::dispatch: pool error in dispatch_batch: JSON-RPC error -1: connection closed
```

- Bot 能連上 Discord（log 顯示 `discord bot connected`）
- 有人發訊息時 kiro-cli 被 spawn 並初始化成功
- 初始化後約 1 秒就斷線，不回覆任何訊息
- 新舊 thread 都一樣失敗

### 根因

在 host 上對 `.kiro/` 目錄執行了 `sudo chown -R kdprogramer:kdprogramer`，導致：

```
.kiro/sessions/  owner 從 1000:1000 (agent) 變成 1002:1002 (kdprogramer)
                 權限 drwxr-xr-x → agent user 只有 r-x，無法寫入
```

kiro-cli 啟動後嘗試在 `.kiro/sessions/cli/` 建立 session 檔案 → 寫入權限被拒 → crash → openab 收到 `connection closed`。

### 為什麼會改權限

為了讓 `git checkout` / `git reset --hard` 能寫入 `.kiro/steering/` 下的檔案（它們被容器的 agent user 佔住）。

### 修復

```bash
sudo chown -R 1000:1000 /path/to/agents/keding-dc/<bot-name>/.kiro/sessions/
sudo chown 1000:1000 /path/to/agents/keding-dc/<bot-name>/.kiro/settings/
sudo chown 1000:1000 /path/to/agents/keding-dc/<bot-name>/.kiro/
kubectl rollout restart deployment/keding-dc-<bot-name> -n bikini-bottom
```

### 教訓

1. **永遠不要對 `.kiro/sessions/` 改 owner** — 這個目錄必須是 uid 1000 (agent) 可寫
2. **需要修改 steering 檔案時**，只改 `.kiro/steering/` 的權限，不要用 `-R` 打整個 `.kiro/`：
   ```bash
   # ✅ 正確：只改 steering
   sudo chown -R kdprogramer:kdprogramer .kiro/steering/
   
   # ❌ 錯誤：改整個 .kiro（sessions 被波及）
   sudo chown -R kdprogramer:kdprogramer .kiro/
   ```
3. **改完 steering 後要把 owner 改回去**：
   ```bash
   sudo chown -R 1000:1000 .kiro/steering/
   ```
   或者用 `kubectl cp` 把檔案丟進 Pod，完全不動 host 權限。

### 相關誤判

排查過程中做了以下**無效操作**（這些都不是原因）：
- 刪除 session 檔案 — 加劇問題（thread_map 指向不存在的 session）
- 清空 thread_map — 沒用，新 session 也寫不進去
- 移除 kd-share volume — 沒用，跟 volume 無關
- 懷疑 KIRO API Key — key 有效（whoami 能通過）
- 懷疑 MCP server 連不上 — 連線正常（405）
- 懷疑 steering 檔案損壞 — UTF-8 正常無 null bytes
