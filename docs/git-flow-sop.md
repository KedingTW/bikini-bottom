# Git Flow 標準作業流程

> 所有涉及程式碼修改的工作都遵循此流程，無論來源是 Redmine issue、Discord 口頭交辦、或 hotfix 需求。
> Agent 和人類開發者都適用。

## 流程總覽

```
收到需求（任何來源）
  ↓
開分支（從 master）
  ↓
開發 + commit
  ↓
push + 開 PR
  ↓
Code review（人類審查）
  ↓
修正 review 意見（如有）
  ↓
PR 合併
```

## 一、分支命名規則

格式：`<角色別名>_<YYYYMMDD>_<簡短描述>`

- 角色別名：`bob`、`patrick` 等
- 日期：開分支當天
- 簡短描述：英文小寫，多個單字用 `-` 連接，描述這次修改的內容

範例：
- `bob_20260416_add-login-api`
- `patrick_20260416_fix-db-connection`
- `bob_20260416_hotfix-null-check`

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
- 一個任務對應一個分支

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
gh pr create --title "簡短描述" --body "說明這次修改的內容和原因"
```

- PR 標題使用繁體中文
- PR 描述說明修改內容和原因
- 如果有對應的 Redmine issue，在描述中附上編號（非必要）

### 步驟 4：Code Review

- PR 由人類審查
- 如果有修正意見，在同一分支上修改後 push
- 修正完成後在 PR 留言通知 reviewer

### 步驟 5：PR 合併

- PR 通過後由 reviewer 合併（或 Agent 自行合併，視團隊約定）
- 合併後分支自動刪除（GitHub 設定）

## 三、特殊情況

### 衝突處理

- push 前先 `git pull origin master --rebase`
- 如果有衝突無法自行解決，在 Discord 中回報，不要強制 push

### 多人協作同一任務

- 原則上一個任務一個人負責
- 如果需要多人協作，各自開分支，先合併的人負責處理衝突

## 四、工具需求

| 工具 | 用途 | 安裝狀態 |
|------|------|----------|
| `git` | 版本控制 | ✅ 已安裝（Dockerfile） |
| `gh` | GitHub CLI（開 PR、管理 PR） | ✅ 已安裝（Dockerfile） |

### gh 認證

Agent 容器首次啟動後需要執行：

```bash
docker exec -it <容器名稱> gh auth login
```

選擇 GitHub.com → HTTPS → 用 browser 認證。

## 五、與 Redmine 的搭配（選用）

當任務來自 Redmine issue 時，Git Flow 結束後額外做：
- 在 Redmine issue 留言附上 PR 連結
- 更新 Redmine issue 狀態為 review

這部分由 Redmine SOP 規範，不屬於 Git Flow 本身的範疇。
