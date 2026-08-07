# 事故報告：章魚哥無法回應

| 項目 | 內容 |
|------|------|
| 日期 | 2026-08-03 |
| 影響範圍 | squidward（章魚哥）完全無法回應 Discord 訊息 |
| 持續時間 | 自 admin image 上次部署至今（未確認確切起始時間） |
| 嚴重度 | 高（角色完全失效） |

---

## 症狀

- Discord @ 章魚哥，他出現 👀 反應但不回覆
- Pod 狀態顯示 Running，Discord bot 也成功連線
- 但 log 中出現：
  ```
  [kiro-key-wrap] pick HTTP error: 405
  [kiro-key-wrap] ERROR: no key available (admin unreachable or pool empty)
  openab::dispatch: pool error in dispatch_batch: JSON-RPC error -1: connection closed
  ```

---

## 根因分析

### 呼叫鏈

```
Discord 訊息進來
  → openab 收到，觸發 agent session
    → 執行 kiro-key-wrap（config.toml 中 command = "kiro-key-wrap"）
      → POST http://admin:8501/api/key-pool/pick  ← 這裡斷了
        → admin 回 405 Method Not Allowed
      → kiro-key-wrap 拿不到 key，exit(1)
    → openab 收到 connection closed，放棄該 session
```

### 為什麼 admin 回 405？

PR #82（`patrick_20260721_key-pool-coordinator`）在 2026-07-21 左右合併到 GitHub master，新增了：
- `services/admin/backend/key_pool.py` — key pool 邏輯
- `app.py` 中 `app.include_router(key_pool_router, prefix="/api/key-pool")` — 註冊路由

但**線上跑的 admin image 是在 PR #82 合併之前 build 的**，所以：
- image 裡的 app.py 沒有 `/api/key-pool/` 路由
- FastAPI 對不認識的路徑回 405（因為有其他路由前綴部分匹配）

### 為什麼 image 沒更新？

- 本機 master 分支停在 `7f5885e`（PR #81），沒有 pull 到 PR #82 的合併 commit `574dccd`
- admin image tag 是 `latest`，沒有版本號綁定，所以沒人注意到它過時了
- PR #82 合併後沒有觸發 rebuild + redeploy 流程

---

## 修復步驟

1. `git fetch origin master` — 拉到含 key-pool 的最新 master
2. `git checkout origin/master -- services/admin/` — 更新本機 admin 原始碼
3. 修正 MySQL strict mode 問題：
   - `app.py` 第 302 行 `description TEXT DEFAULT ''` → `description TEXT`
   - MySQL strict mode 不允許 TEXT/BLOB 欄位設 default value
4. `docker build --no-cache -t bikini-bottom/admin:latest` — 重新建構 image
5. `docker save | sudo k3s ctr images import -` — 匯入 k3s
6. 刪除舊 admin pod，等新 pod Running
7. `kubectl rollout restart deployment squidward` — 重啟章魚哥
8. 確認 log 中不再出現 key-pool error，Discord 回應正常

---

## 待辦

- [ ] 把 `description TEXT DEFAULT ''` → `description TEXT` 的修正 commit 回 master
- [ ] 考慮 admin image 加版本 tag（不要只用 latest），或加 CI 自動 rebuild
- [ ] PR 合併到 master 後，應有流程提醒 rebuild 受影響的 image

---

## 教訓

1. **Key Pool 是 agent 啟動的前置依賴** — admin 掛了或缺 endpoint，所有用 `kiro-key-wrap` 的角色都會失效
2. **合併 PR ≠ 部署上線** — 沒有 CI/CD 自動 rebuild 的情況下，合併後必須手動 build + deploy
3. **image:latest 沒有版本追蹤** — 看不出線上跑的是哪個 commit 的產物
