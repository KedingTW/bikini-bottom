# ⚠️ 鐵律（每次 session 必讀）

1. **Mention 檢查**：回覆前最後一步——我需要 mention 誰？需要就 mention，不確定就 mention。漏 mention = 流程卡死。
2. **禁止 commit 的檔案**：`_status.md`、`_archive.md`、`_projects.md`、`.env` 絕對不能 git add。commit 前跑 `git status` 確認。
3. **時區**：所有時間以台灣時間 (Asia/Taipei, UTC+8) 回答。不要用 UTC。
4. **不自行合併 PR**：不執行 `gh pr merge`、`git merge` 到 develop 或 master。
5. **不 force push**：不使用 `git push --force`。
