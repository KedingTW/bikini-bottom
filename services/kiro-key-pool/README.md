# Kiro API Key Pool

Kiro API Key 輪替池，借鑑 [kiro-multi](https://github.com/wangyuyan-agent/kiro-multi) 的 wrapper + pool 設計，
簡化為 API Key 模式，適用於比奇堡的 k3s 容器化部署。

## 運作原理

```
openab → spawn "kiro-key-wrap acp --trust-all-tools"
                    │
                    ├─ 1. flock 加鎖
                    ├─ 2. 從 keys.json 中 round-robin 選一把可用的 key
                    ├─ 3. KIRO_API_KEY=$selected exec kiro-cli
                    ├─ 4. session 結束後檢查 stderr
                    └─ 5. 偵測到 quota/rate-limit → 標記該 key exhausted
```

## 檔案結構

```
/etc/kiro-pool/keys.json      ← ConfigMap mount（key 清單）
/data/kiro-pool/state.json    ← shared hostPath（輪替狀態）
/data/kiro-pool/state.lock    ← flock 用
/data/kiro-pool/logs/         ← 撞牆時的 stderr tail
/usr/local/bin/kiro-key-wrap  ← wrapper script
/usr/local/lib/kiro-pool/     ← pick.py, mark_exhausted.py
```

## 加 key

1. 編輯 `keys.json`（或 kubectl edit configmap kiro-key-pool）
2. 新的 session 自然會用到新 key，不用重啟 bot

## 移除 key

1. 從 `keys.json` 中移除
2. 進行中的 session 不受影響（它們已經拿到 key 了）
3. 新 session 不會再選到它

## 撞牆後的行為

- 偵測到 stderr 中的 rate-limit / quota 訊息 → 標記 exhausted
- 該 key 不再被 pick，直到下個月 1 號自動解凍
- 進行中的 session 不受影響（已結束的那個才觸發標記）

## 環境變數

| env | 說明 | 預設值 |
|-----|------|--------|
| KIRO_POOL_KEYS | keys.json 路徑 | /etc/kiro-pool/keys.json |
| KIRO_POOL_STATE | state.json 路徑 | /data/kiro-pool/state.json |
| KIRO_POOL_LOCK | lock file 路徑 | /data/kiro-pool/state.lock |
| KIRO_POOL_LOGS | log 目錄 | /data/kiro-pool/logs |
| AGENT_NAME | 呼叫的 agent 名稱 | unknown |

## 觀察狀態

```bash
# 在 k3s node 上
cat /home/kdprogramer/kiro-pool/state.json | python3 -m json.tool

# 看哪些 key 被標記 exhausted
jq '.keys | to_entries[] | select(.value.exhausted)' /home/kdprogramer/kiro-pool/state.json

# 看最近的撞牆 log
ls -lt /home/kdprogramer/kiro-pool/logs/ | head
```
