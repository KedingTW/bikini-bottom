# ALS MCP Daily Report — 開發規格文件

## 需求

讓 ALS MCP Server 支援查詢個人日報內容，支持指定時間範圍。權限邏輯完全沿用 als-api 現有機制。

---

## 開發階段

| 階段 | Repo | 內容 | 條件 |
|------|------|------|------|
| 1 | als-api | impersonate endpoint（解決 token 認證問題） | 詠仁確認後開工 |
| 2 | als-mcp-server | tool + token 管理 + repository（打現有日報 API） | 階段 1 通過 review 後 |

---

## 階段 1：als-api 端（僅 impersonate）

### 目的

解決 MCP server 在 wecom token 來源下，只有 employee_id 沒有 als access_token 的問題。

### Impersonate Endpoint

| 項目 | 值 |
|------|---|
| 路由 | `POST /api/mcp/impersonate` |
| 認證 | Header `X-Service-Key: {MCP_SERVICE_KEY}` |
| Middleware | 新增 `mcp_service_auth`（驗 X-Service-Key） |
| Controller | `McpAuthController@impersonate` |

**Request：**
```json
{
  "employee_id": "KD001234"
}
```

**Response：**
```json
{
  "access_token": "01D9BCF4-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "expires_in": 3600
}
```

**行為：**
1. 驗證 `X-Service-Key` 合法（比對環境變數 `MCP_SERVICE_KEY`）
2. 根據 `employee_id` 查找 user record
3. 產生 UUID 格式 access_token
4. 存入 Redis：key = `user_{access_token}`，value = user 資料，TTL = 3600s
5. 回傳 token

**重要：**
- 不覆蓋使用者既有 token（Redis key 以 token 值為 key，各自獨立）
- 不限 scope，token 等同正常登入 token
- als-api 不需要新增任何日報相關 endpoint，現有的日報 API 直接沿用

### 環境變數

| 變數 | 說明 |
|------|------|
| `MCP_SERVICE_KEY` | 驗證 impersonate 請求來源，僅 MCP server 持有 |

### Auth Middleware 修改（Authenticate.php）

**決策（珈瑄確認）**：既有單一登入限制不改變，僅對 MCP token 放寬。

**修改方式**：加 Redis fallback 路徑

```
原有流程：
  token → 查 DB access_token 比對 → 通過/拒絕

修改後：
  token → 查 DB access_token 比對 → 通過 → 放行（不變）
                                   → 失敗 → fallback 查 Redis user_{token}
                                              → 存在 → 從 Redis 取 user 資料，認證通過
                                              → 不存在 → 401
```

- 一般登入 token：走 DB 比對，單一登入限制不變
- MCP impersonate token：DB 比對失敗，Redis fallback 通過
- 無效 token：兩條路都失敗，401

### 錯誤回傳

| HTTP Status | 情境 |
|-------------|------|
| 401 | X-Service-Key 無效 |
| 404 | employee_id 找不到對應 user |
| 422 | 缺少 employee_id 參數 |

---

## 階段 2：als-mcp-server 端（階段 1 通過後執行）

### Tool：`GetDailyReport`

**Tool 參數（agent 傳入）：**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | string | ✅ | 起始日期 YYYY-MM-DD |
| end_date | string | ✅ | 結束日期 YYYY-MM-DD |

> als_access_token 由 MCP server 從認證 context 自動取得，agent 不需傳入。

**MCP server 呼叫 als-api 現有端點：**

| als-api 端點 | 用途 |
|-------------|------|
| `POST /api/daily_report/list` | 取得日報列表及內容 |

> 直接打現有 API，Bearer token 認證，權限邏輯由 als-api 現有機制處理。

**回傳（MCP tool 精簡後）：**

```json
{
  "user_name": "王小明",
  "department": "系統開發課",
  "reports": [
    {
      "report_date": "2026-06-03",
      "status": "submitted",
      "work_items": [
        {
          "category": "專案開發",
          "content": "完成 MCP 日報 API 串接",
          "hours": 4.0
        }
      ],
      "tomorrow_plan": "繼續...",
      "issues": "無",
      "supervisor_comment": "OK",
      "supervisor_commented_at": "2026-06-04 09:15:00"
    }
  ]
}
```

> 回傳格式由 MCP server 端負責精簡（從 als-api 原始回傳中取需要的欄位），不需 als-api 改動。

### Token 管理（Reuse 機制）

MCP server 維護 cache：`employee_id → { mcp_token, expires_at }`

流程：
1. 識別使用者來源（als token 直接用 / wecom token 取得 employee_id）
2. wecom 來源：檢查 cache 有無有效 token
3. cache hit → 使用現有 token
4. cache miss → 呼叫 impersonate 取得新 token，存入 cache
5. 帶 token 打 als-api **現有**日報端點

### 架構（預留擴充）

```
app/
├── Mcp/Tools/Als/DailyReport/
│   └── AlsDailyReportListTool.php
├── Models/Als/DailyReport/
│   ├── AlsDailyReportListBuilderModel.php
│   └── AlsDailyReportListModel.php
├── Repositories/Als/DailyReport/
│   ├── AlsDailyReportRepositoryInterface.php
│   └── AlsDailyReportRepository.php
└── Services/Als/DailyReport/
    └── AlsDailyReportService.php
```

**Interface 預留：**

```php
interface AlsDailyReportRepositoryInterface
{
    public function getPersonalList(array $options): object;
    // 未來擴充：
    // public function getSubordinateList(array $options): object;
    // public function submitReview(array $options, int|string $id): object;
}
```

---

## 認證流程圖

```
Agent → MCP Server → [token reuse cache]
                  ↓ (cache miss, wecom來源)
            POST /mcp/impersonate
            X-Service-Key + employee_id
                  ↓
            取得 als access_token (1hr TTL)
                  ↓
            POST /daily_report/list  ← 現有 API，不改
            Bearer: access_token
                  ↓
            als-api Auth::id() → 權限判斷 → 回傳日報
```

---

## 未來擴充方向（本次不做，架構已預留）

| 功能 | als-api 現有端點 | 新增 MCP Tool |
|------|-----------------|--------------|
| 查看下屬日報 | `POST /daily_report_view/list` | `GetSubordinateDailyReport` |
| 批閱日報 | `POST /daily_report_view/assign/update` | `ReviewDailyReport` |

> 因為 impersonate token 不限 scope，未來擴充只需在 mcp-server 加 tool，als-api 端不需再改。
