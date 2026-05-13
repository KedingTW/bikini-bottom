# MCP 工具

## Redmine

- `get_redmine_issue` / `list_redmine_issues` — 查詢
- `create_redmine_issue` / `update_redmine_issue` — 建立/更新
- `list_redmine_projects` / `list_project_members` — 專案資訊

### 關鍵注意

- 留言和狀態更新必須分開呼叫
- 留言用純文字，不用 markdown/emoji
- 建立 issue 時指派給開發者，追蹤標籤用「功能」
- 狀態 ID：1=尚未開發, 2=開發中, 9=review, 3=已完成
