# GitHub 工具使用指南

## 認證

你的容器透過 `GH_TOKEN` 環境變數自動認證 GitHub，不需要手動登入。

## 常用指令

### 讀取 PR 資訊

```bash
# 查看 PR 基本資訊（JSON 格式）
gh pr view <PR編號> --repo <owner/repo> --json title,body,files,commits,labels,comments

# 查看 PR diff
gh pr diff <PR編號> --repo <owner/repo>

# 查看 PR 的 comment 列表
gh pr view <PR編號> --repo <owner/repo> --comments
```

### 留下 Review Comment

```bash
# 留下一般 comment
gh pr comment <PR編號> --repo <owner/repo> --body "review 內容"
```

注意：目前共用同一組 GitHub PAT，無法使用 `gh pr review --request-changes` 或 `--approve`（同帳號限制）。
未來獨立帳號後可改用：
```bash
# 未來可用
gh pr review <PR編號> --repo <owner/repo> --request-changes --body "需要修改"
gh pr review <PR編號> --repo <owner/repo> --approve --body "通過"
```

### 讀取 Repo 檔案（需要更多上下文時）

```bash
# 讀取特定檔案內容（從 PR 的 head branch）
gh api repos/<owner>/<repo>/contents/<path>?ref=<branch> --jq '.content' | base64 -d

# 讀取 .github/REVIEW_CONTEXT.md（專案審查規則）
gh api repos/<owner>/<repo>/contents/.github/REVIEW_CONTEXT.md --jq '.content' | base64 -d
```

### 操作標籤

```bash
# 移除標籤
gh pr edit <PR編號> --repo <owner/repo> --remove-label "ai code review"

# 加上標籤
gh pr edit <PR編號> --repo <owner/repo> --add-label "awaiting review"
```

## 錯誤處理

- 指令失敗時最多重試 2 次
- 如果 `gh auth` 未設定或過期，在 Discord 中回報，不要嘗試自行登入
- 如果 repo 不存在或無權限，在 Discord 中回報

## 注意事項

- 不要 clone repo，用 `gh` 指令遠端操作即可
- 不要修改任何程式碼
- 不要合併 PR
- 不要建立分支或 commit
