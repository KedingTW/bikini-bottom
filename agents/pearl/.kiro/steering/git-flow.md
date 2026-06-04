# Git Flow

## 分支策略

- `master`：正式環境 / `develop`：開發分支
- 一般：從 develop 開分支，PR 目標 develop
- hotfix：從 master 開分支，同時對 master 和 develop 各開一個 PR
- 是否 hotfix 由交辦人告知

## 分支命名

格式：`<角色>_<YYYYMMDD>_<描述>`（英文小寫，底線連接）
hotfix 格式：`<角色>_<YYYYMMDD>_<描述>(hotfix)`
範例：
- 一般：`pearl_20260416_add_login_page`
- hotfix：`pearl_20260522_fix-form-validation(hotfix)`

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

PR title 格式：`<name>_<YYYYMMDD>_<描述>`
- name 一律用**你自己的角色名稱**（即分支名稱的前綴），與分支命名保持一致
- 範例：`pearl_20260522_add_login_page`

```bash
git push origin <分支>
gh pr create --base develop --title "<PR title>" --body "修改說明..."
```

## Code Review（泡芙老師）

1. PR 開好後 mention：`<@1503574146117013555> 請審閱 PR #XX：<連結>`
2. 收到 review → 認同就修，不認同在 PR 留言說明
3. 修完再 mention 泡芙老師
4. 最多 3 輪

## 你的流程終點

你的 PR 流程在以下步驟結束，之後的事不是你的職責：

1. PR 開好 + mention 泡芙老師 review
2. 根據 review 修正（最多 3 輪）
3. 泡芙老師通過後會直接 mention 原 Po（論壇貼文作者），由原 Po 決定後續

**到此為止。** PR 的合併由人類執行。
即使 review 全部通過、即使看起來可以合併——你的工作就是到「等人類合併」為止。
絕對不要執行 `gh pr merge`、`git merge`、或任何合併操作。

## 禁止事項

- **不自行合併 PR**（不執行 gh pr merge / git merge 到 develop 或 master）
- 不在 master/develop 直接 commit
- 不用 `git push --force`
- `gh` 失敗最多重試 2 次，仍失敗就在 Discord 回報

## 禁止 commit 的檔案

以下檔案是本地狀態，絕對不能 `git add`：
- `_status.md`
- `_archive.md`
- `_projects.md`
- `.env`

**commit 前自我檢查**：`git status` 看一眼，有上述檔案就 `git reset HEAD <file>`。
