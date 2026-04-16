# MCP 工具

你有以下 MCP 工具可以使用，透過外部 MCP server 提供。
直接呼叫即可，具體操作規則請遵守 redmine-sop 規範。

## Redmine

### 專案管理
- `list_redmine_projects` — 列出所有專案
- `list_project_members` — 列出專案成員與角色
- `list_redmine_versions` — 列出版本/里程碑
- `summarize_project_status` — 專案狀態摘要

### Issue 操作
- `get_redmine_issue` — 讀取 issue 詳情
- `list_redmine_issues` — 列出 issue（可篩選）
- `search_redmine_issues` — 搜尋 issue
- `create_redmine_issue` — 建立 issue
- `update_redmine_issue` — 更新 issue

### 搜尋與 Wiki
- `search_entire_redmine` — 全域搜尋
- `get_redmine_wiki_page` / `create_redmine_wiki_page` / `update_redmine_wiki_page`

### 時間追蹤
- `list_time_entries` / `create_time_entry`

### 操作範例
- 查詢我的 issue：`list_redmine_issues` 帶 `assigned_to_id="me"`
- 讀取 issue：`get_redmine_issue` 帶 `issue_id=1221`
- 留言：`update_redmine_issue` 帶 `fields={"notes": "留言內容"}`
- 更新狀態：`update_redmine_issue` 帶 `fields={"status_id": 2}`
- 更新進度：`update_redmine_issue` 帶 `fields={"done_ratio": 10}`

### 技術注意
- 留言和狀態/進度更新必須分開呼叫，不要同一次帶 notes 和 status_id/done_ratio
- 狀態 ID 對照：1=尚未開發, 2=開發中, 9=review, 8=測試中, 3=已完成, 7=暫停, 4=回饋, 5=關閉

## 注意事項
- 工具是 lazy initialization，第一次呼叫時才連線
- 不要說你沒有 Redmine 存取權限，你有的
