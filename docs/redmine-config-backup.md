# Redmine 設定備份

> 此檔案記錄被移除的 Redmine 相關設定，將來需要時可依此加回。

## 1. 海綿寶寶 MCP 設定 (`agents/bob/.kiro/settings/mcp.json`)

```json
"redmine": {
  "url": "http://host.docker.internal:9500/sse",
  "autoApprove": ["redmine_request", "redmine_paths_info", "redmine_paths_list"]
}
```

## 2. Kiro MCP 設定 (`.kiro/settings/mcp.json`)

```json
"redmine-test": {
  "url": "http://localhost:9500/mcp",
  "autoApprove": ["get_redmine_issue", "list_redmine_issues", "search_redmine_issues", "create_redmine_issue", "update_redmine_issue", "list_redmine_projects", "list_project_members", "list_redmine_versions", "list_project_issue_custom_fields", "summarize_project_status", "search_entire_redmine", "get_redmine_wiki_page", "create_redmine_wiki_page", "update_redmine_wiki_page", "delete_redmine_wiki_page", "list_time_entries", "create_time_entry", "update_time_entry", "list_time_entry_activities", "get_redmine_attachment_download_url", "cleanup_attachment_files"]
}
```

## 3. 海綿寶寶 Steering (`agents/bob/.kiro/steering/redmine-sop.md`)

```markdown
# Redmine 作業規範

## 狀態對照

| 狀態 | ID | 完成% | 說明 |
|------|-----|-------|------|
| 尚未開發 | 1 | 0% | 已建立未開始 |
| 開發中 | 2 | 10-80% | 進行中 |
| review | 9 | 90% | 等待/進行 code review |
| 已完成 | 3 | 100% | 已部署正式環境 |
| 暫停 | 7 | 維持 | 保留暫停前% |

## 操作規則

- 操作前先讀 issue 現有資訊，避免覆蓋他人更新
- 留言用繁體中文純文字，不用 markdown/emoji（API 會 500）
- 留言和狀態更新必須分開呼叫
- 完成後一律改 review（status_id:9, 90%），不要自行改為已完成
- 你無法估算工時，預估工時留空

## 建立 Issue

- 必填：主旨、追蹤標籤、狀態、指派對象
- 追蹤標籤：功能/修復/規劃/研究/測試（不確定用「功能」）
- 找不到父層或分類 → 不自行建立，在 Discord 回報

## 不確定時

- 維持現狀，在 Discord 詢問
- 不要自行猜測或假設
```

## 4. 海綿寶寶 Workflow Redmine 段落 (`agents/bob/.kiro/steering/workflow.md`)

```markdown
## Redmine 任務處理

收到 Redmine issue 時：
1. 讀 issue → 確認理解 → 在 Discord 簡述處理計畫
2. 等確認後開始 → 更新 issue 狀態為開發中（status_id:2, 10%）
3. 執行任務 → 完成後在 issue 留言回報
4. 狀態改為 review（status_id:9, 90%）
```

## 5. 派大星 Workflow Redmine 段落 (`agents/patrick/.kiro/steering/workflow.md`)

```markdown
## Redmine 任務處理

收到 Redmine issue 時：
1. 讀 issue → 確認理解 → 在 Discord 簡述處理計畫
2. 等確認後開始 → 更新 issue 狀態為開發中（status_id:2, 10%）
3. 執行任務 → 完成後在 issue 留言回報
4. 狀態改為 review（status_id:9, 90%）
```

## 6. 章魚哥 MCP Tools (`agents/squidward/.kiro/steering/mcp-tools.md`)

```markdown
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
```

## 7. 章魚哥 Workflow Redmine 段落 (`agents/squidward/.kiro/steering/workflow.md`)

```markdown
## 交辦開發任務

1. 確認規格已 push
2. 建立 Redmine issue（描述中標明規格路徑）
3. Discord mention 開發者：「@bob 新任務 Redmine #XXX，規格在 <路徑>」

## 規格變更（開發中途）

1. 更新規格文件，push
2. 在 Redmine issue 留言通知變更
3. Discord mention 受影響的開發者
```

## 8. .env Redmine 環境變數

```
# Redmine MCP（POC）
REDMINE_URL=http://192.168.1.84:800
REDMINE_API_KEY_BOB=062ea215e79489ef793b9913d60dc16cf4982436
```

## 9. shared/steering/security.md 提及

```markdown
- Redmine API Key
```

## 10. shared/steering/channel-handoff.md 提及

```markdown
4. **參考**：相關文件路徑、PR 連結、或 Redmine issue 編號
```
