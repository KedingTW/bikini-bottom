# Git Flow 標準作業流程

> 適用於 Redmine 任務涉及程式碼修改時的完整流程。
> Agent 和人類開發者都遵循此流程。

## 流程總覽

```
Redmine issue 指派
  ↓
開分支（從 master）
  ↓
開發 + commit
  ↓
push + 開 PR
  ↓
Redmine 狀態 → review
  ↓
Code review（人類審查）
  ↓
修正 review 意見（如有）
  ↓
PR 合併
  ↓
Redmine 狀態 → 測試中（由驗收方觸發）
  ↓
Redmine 狀態 → 已完成（由驗收方觸發）
```

## 一、分支命名規則

格式：`<角色別名>_<YYYYMMDD>_<簡短描述>`

- 角色別名：`bob`、`patrick` 等
- 日期：開分支當天
- 簡短描述：英文小寫，多個單字用 `-` 連接，對應 Redmine issue 的任務內容

範例：
- `bob_20260416_add-login-api`
- `patrick_20260416_fix-db-connection`

> 注意：Kiro IDE 的分支命名格式為 `kiro_<YYYYMMDD>_<描述>`，
> Agent 的分支命名格式為 `<角色別名>_<YYYYMMDD>_<描述>`，兩者不同。

## 二、開發流程

### 步驟 1：開分支

```bash
git checkout master
git pull origin master
git checkout -b <分支名稱>
```

- 一律從 `master` 最新版本開分支
- 一個 Redmine issue 對應一個分支

### 步驟 2：開發與 commit

```bash
git add <檔案>
git commit -m "feat: 簡短描述"
```

- commit message 使用繁體中文
- 格式：`feat/fix/chore/docs: 簡短描述`
- 可附多行說明，第二行空行後寫詳細內容
- 開發過程中可以多次 commit，不需要 squash

### 步驟 3：push 並開 PR

```bash
git push origin <分支名稱>
gh pr create --title "簡短描述" --body "相關 Redmine issue: #<issue編號>"
```

- PR 標題使用繁體中文
- PR 描述中附上 Redmine issue 編號
- 開完 PR 後，將 Redmine issue 狀態改為「review」（status_id: 9），完成百分比 90%
- 在 Redmine issue 留言附上 PR 連結

### 步驟 4：Code Review

- PR 由人類審查
- 如果有修正意見，在同一分支上修改後 push
- 修正完成後在 PR 留言通知 reviewer

### 步驟 5：PR 合併

- PR 通過後由 reviewer 合併（或 Agent 自行合併，視團隊約定）
- 合併後分支自動刪除（GitHub 設定）

### 步驟 6：後續狀態更新

- 「測試中」和「已完成」由驗收方觸發，Agent 不自行更新
- Agent 的責任到 PR 開出 + Redmine 狀態改為 review 為止

## 三、特殊情況

### 不涉及程式碼的任務

- 純研究、文件撰寫、數學計算等不需要開分支
- 直接在 Redmine 上回報結果即可
- 狀態流轉依 redmine-sop 規範

### 衝突處理

- push 前先 `git pull origin master --rebase`
- 如果有衝突無法自行解決，在 Discord 中回報，不要強制 push

### 多人協作同一 issue

- 原則上一個 issue 一個人負責
- 如果需要多人協作，各自開分支，先合併的人負責處理衝突

## 四、工具需求

| 工具 | 用途 | 安裝狀態 |
|------|------|----------|
| `git` | 版本控制 | ✅ 已安裝（Dockerfile） |
| `gh` | GitHub CLI（開 PR、管理 PR） | ⬜ 需安裝（Dockerfile 更新） |

### gh 認證

Agent 容器首次啟動後需要執行：

```bash
docker exec -it <容器名稱> gh auth login
```

選擇 GitHub.com → HTTPS → 用 browser 認證。

## 五、Redmine 狀態與 Git Flow 對應

| Git Flow 階段 | Redmine 狀態 | 完成百分比 |
|---------------|-------------|-----------|
| 開分支、開發中 | 開發中 | 10–80% |
| push + 開 PR | review | 90% |
| Code review 進行中 | review | 90% |
| PR 合併後 | （由驗收方更新） | — |
| 部署測試環境 | 測試中 | 90% |
| 部署正式環境 | 已完成 | 100% |
