# Git Flow 作業規範

## 一、適用時機

- 當 Redmine 任務涉及程式碼修改時，必須走 Git Flow
- 純研究、文件撰寫、數學計算等不涉及程式碼的任務，不需要走 Git Flow

## 二、分支規則

- 一律從 master 最新版本開分支
- 一個 Redmine issue 對應一個分支
- 分支命名格式：`<你的角色別名>_<YYYYMMDD>_<簡短描述>`
  - 角色別名就是你的英文名字小寫（例如 bob、patrick）
  - 日期是開分支當天
  - 簡短描述用英文小寫，多個單字用 `-` 連接
  - 範例：`bob_20260416_add-login-api`

## 三、開發流程

### 開分支
```bash
git checkout master
git pull origin master
git checkout -b <分支名稱>
```

### commit
- commit message 使用繁體中文
- 格式：`feat/fix/chore/docs: 簡短描述`
- 開發過程中可以多次 commit

### push 並開 PR
```bash
git push origin <分支名稱>
gh pr create --title "簡短描述" --body "Redmine issue #<編號>"
```
- PR 標題使用繁體中文
- PR 描述附上 Redmine issue 編號

### 開完 PR 後
- Redmine issue 狀態改為 review（status_id: 9），完成百分比 90%
- 在 Redmine issue 留言附上 PR 連結（純文字，例如「PR 已開：https://github.com/...」）

## 四、Code Review 回應

- 如果 reviewer 在 PR 留下修正意見，在同一分支上修改後 push
- 修正完成後在 PR 留言通知 reviewer
- 不要開新分支或新 PR

## 五、衝突處理

- push 前先 `git pull origin master --rebase`
- 如果有衝突無法自行解決，在 Discord 中回報，不要強制 push（不要用 `--force`）

## 六、你不需要做的事

- 不要自行合併 PR（除非被明確授權）
- 不要自行將 Redmine 狀態改為「測試中」或「已完成」
- 不要在 master 上直接 commit
- 不要用 `git push --force`

## 七、錯誤處理

- `gh` 指令失敗時，最多重試 2 次
- 如果 `gh auth` 未設定或過期，在 Discord 中回報，不要嘗試自行登入
- `git push` 被拒絕時，先嘗試 rebase，rebase 失敗就在 Discord 中回報
