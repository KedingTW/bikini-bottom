# Agent Git 身份區分方案

> 目標：讓多個 agent 共用同一個 GitHub PAT 時，能在 commit 歷史中區分操作者身份。

---

## 現況

- 所有 agent（bob, patrick, sandy, larry...）共用同一個 GitHub PAT
- `.gitconfig` 中均未設定 `[user]` 區塊
- 結果：所有 commit 在 GitHub 上顯示為同一人

---

## 方案比較

| 方案 | 複雜度 | 效果 | 適用場景 |
|------|--------|------|----------|
| Git Author 設定 | ⭐ 低 | commit 歷史區分 author | 立即可用，推薦先做 |
| Commit message prefix | ⭐ 低 | 訊息中辨識 | 搭配方案一 |
| GitHub App token | ⭐⭐⭐ 高 | 完整獨立身份 + bot 標籤 | 長期正規做法 |
| Machine User 帳號 | ⭐⭐ 中 | 完全獨立帳號 | 需要獨立 push 身份時 |

---

## 方案一：Git Author 設定（推薦立即執行）

### 作法

在每個 agent 的 `.gitconfig` 加入 `[user]` 區塊：

```ini
# agents/bob/.gitconfig
[user]
    name = "bob [bot]"
    email = "bob-agent@openab.local"

# agents/patrick/.gitconfig
[user]
    name = "patrick [bot]"
    email = "patrick-agent@openab.local"

# agents/sandy/.gitconfig
[user]
    name = "sandy [bot]"
    email = "sandy-agent@openab.local"

# agents/larry/.gitconfig
[user]
    name = "larry [bot]"
    email = "larry-agent@openab.local"

# agents/squidward/.gitconfig
[user]
    name = "squidward [bot]"
    email = "squidward-agent@openab.local"

# agents/puff/.gitconfig
[user]
    name = "puff [bot]"
    email = "puff-agent@openab.local"
```

### 搭配 config.toml 環境變數繼承

確保 `inherit_env` 包含 Git 相關變數（已在部分 agent 設定）：

```toml
[agent]
inherit_env = ["GH_TOKEN", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"]
```

### GitHub 顯示效果

- commit 頁面會顯示 `bob [bot] authored`
- 因為 email 不對應 GitHub 帳號，頭像為灰色預設圖
- push 記錄仍為你的 PAT 帳號（不影響權限）

### 注意事項

- email domain 建議統一用 `@openab.local`（不存在的 domain，不會收到通知）
- 如果想要有頭像，可以用 GitHub noreply email 格式：`ID+username@users.noreply.github.com`
- 修改 `.gitconfig` 後需要 `docker compose restart <agent>` 才生效

---

## 方案二：Commit Message Prefix

在 agent 的 steering/workflow 中要求 commit message 加前綴：

```
[bob] feat: add order validation
[patrick] fix: webhook retry logic
```

或使用 Git trailer：

```
feat: add order validation

Operated-by: bob
```

---

## 方案三：GitHub App（長期方案）

1. 在 GitHub 建立一個 GitHub App（例如 `BikiniBottom Bot`）
2. 安裝到你的 org/repos
3. 用 App 的 private key 為每個 agent 產生 installation token
4. Commit 會顯示為 `bikini-bottom-bot[bot]` + 專屬 bot 圖標

優點：
- GitHub 原生 bot 標籤
- 可設定細粒度權限
- 不占用 PAT rate limit

缺點：
- 需管理 private key 和 token refresh（每小時過期）
- 所有 agent 共用同一個 App 身份（除非建多個 App）

---

## 方案四：Machine User 帳號

為每個 agent 建立獨立 GitHub 帳號，各自產生 PAT。

優點：
- 完全獨立身份，包括 push 記錄和頭像
- 可以互相 approve PR

缺點：
- 管理多組帳號/2FA
- 私有 repo 需分別授權
- GitHub ToS 不鼓勵大量建立

---

## 執行步驟（方案一）

1. 編輯各 agent 的 `.gitconfig`，加入 `[user]` 區塊
2. 確認 `config.toml` 的 `inherit_env` 包含 Git 變數
3. `docker compose restart bob patrick sandy larry squidward puff`
4. 測試：讓各 agent 做一個測試 commit，確認 `git log --format='%an <%ae>'` 顯示正確
5. 確認 GitHub 上 commit 頁面的 author 顯示

---

## ghpool 是否需要？

**目前不需要。** ghpool 解決的是：
- 多 PAT 的 rate limit 池化（你目前只用一個 PAT，沒有 rate limit 問題）
- 讀取快取（你的 agent 併發量還沒到需要快取的程度）

**什麼時候才需要 ghpool：**
- 當你的 agent 數量成長到 rate limit 成為瓶頸（單 PAT 5000 req/hr）
- 當你有多組 PAT 需要自動輪替
- 當你的 agent 大量重複查詢同一個 repo（快取有價值）

**注意：ghpool 不解決身份區分問題。** 即使用了 ghpool，讀取都走池化 token，寫入才走 client token — 它的設計是為了效率，不是為了身份。
