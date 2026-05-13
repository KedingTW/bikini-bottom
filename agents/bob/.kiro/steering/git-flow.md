# Git Flow

## 分支策略

- `master`：正式環境 / `develop`：開發分支
- 一般：從 develop 開分支，PR 目標 develop
- hotfix：從 master 開分支，同時對 master 和 develop 各開一個 PR
- 是否 hotfix 由交辦人告知

## 分支命名

格式：`<角色>_<YYYYMMDD>_<描述>`（英文小寫，底線連接）
範例：`bob_20260416_add_login_api`

## 開發流程

```bash
# 一般
git checkout develop && git pull origin develop && git checkout -b <分支>

# hotfix
git checkout master && git pull origin master && git checkout -b <分支>
```

- commit message 繁體中文，格式：`feat/fix/chore/docs: 簡短描述`
- push 前先 rebase：`git pull origin develop --rebase`

## PR

PR body 開頭必須包含：
```
[bot-meta]
discord: <當前討論串ID>
user: <交辦人UID>
bot: <你的UID>

修改說明...
```

```bash
git push origin <分支>
gh pr create --base develop --title "<分支名>" --body "<上述格式>"
```

## Code Review（泡芙老師）

1. PR 開好後 mention：`<@1503574146117013555> 請審閱 PR #XX：<連結>`
2. 收到 review → 認同就修，不認同在 PR 留言說明
3. 修完再 mention 泡芙老師
4. 最多 3 輪

## 禁止事項

- 不自行合併 PR
- 不在 master/develop 直接 commit
- 不用 `git push --force`
- `gh` 失敗最多重試 2 次，仍失敗就在 Discord 回報
