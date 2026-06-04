# 裝修小武郎觀看心得 — 後端 API 規格（最終版）

> 狀態：**已確認**  
> 最後更新：2026-05-28

## 需求背景

台灣有寫日報的**課級以上主管（含副課長）**，每月 9 號到下個月 8 號前需要撰寫「裝修小武郎」的觀看心得。撰寫方式同共讀計畫（`reading_plan` 欄位），影片標題包含關鍵字「大小宅」或「武哥」。

## 方案：整合進現有共讀計畫 API

不新增獨立查閱/稽核 API，改為修改現有 5 支 API + 新增 1 支推播 API。

---

## 修改現有 API

### 1. `shared_reading_report/list` — 取得共讀計畫清單

**修改內容**：
- 人員範圍擴大：原有共讀人員 + 台灣課級以上（`permission_title.sort <= 10` + `hrs_code = 'SCS001'`）取聯集
- 心得判斷加入武哥：`videoTitle` 含「大小宅」或「武哥」→ `category = 'renovation_warrior'`，其他 → `category = 'shared_reading'`
- Response 每筆資料加 `category` 欄位（前端不需用它做區分）

### 2. `shared_reading_report/export` — 匯出共讀計畫清單

**修改內容**：
- 資料範圍同 list（包含共讀 + 武哥）
- 匯出欄位**維持原本**，不加 category 欄位

### 3. `shared_reading_report/mark` — 標註

**修改內容**：
- Request 加 `category` 參數（`shared_reading` / `renovation_warrior`）
- 寫入 `shared_reading_plan_mark` 表時帶入 category

### 4. `shared_reading_report_export/list` — 取得共讀心得稽核清單

**修改內容**：
- 稽核清單同時包含共讀心得 + 武哥心得
- 人員範圍取聯集
- Response 每筆資料加 `category` 欄位

### 5. `shared_reading_report_export/export` — 匯出共讀心得稽核清單

**修改內容**：
- Excel 分**兩個 Sheet**：共讀心得 / 武哥心得
- 各 Sheet 內容格式維持原本

---

## 新增 API

### 6. `renovation_warrior_report_export/send` — 推播通知未繳交人員

```
POST /daily_report_view/renovation_warrior_report_export/send
```

#### Request Body

```json
{
  "search": {
    "search_month": "2026-05"
  }
}
```

#### 行為

篩選台灣課級以上主管中尚未繳交武哥心得的人員，依國家分組發送推播通知（繁/簡/英三語）。

---

## 核心邏輯

### 人員範圍

| 類別 | 範圍 |
|------|------|
| 共讀計畫 | 台灣+大陸全體 + 海外領班級以上（現有邏輯不變） |
| 武哥 | 台灣（`hrs_code = 'SCS001'`）+ 課級以上（`permission_title.sort <= 10`） |
| list/稽核清單 | 兩者取**聯集** |

### 心得分類判斷

```
reading_plan 為有效 JSON 且：
  videoTitle 含「大小宅」OR「武哥」→ category = 'renovation_warrior'
  其他 → category = 'shared_reading'
```

DB 層條件：
```sql
-- 武哥心得
WHERE JSON_VALID(reading_plan)
  AND (
    JSON_UNQUOTE(JSON_EXTRACT(reading_plan, '$.videoTitle')) LIKE '%大小宅%'
    OR JSON_UNQUOTE(JSON_EXTRACT(reading_plan, '$.videoTitle')) LIKE '%武哥%'
  )
```

### 標註表 Migration

```sql
ALTER TABLE shared_reading_plan_mark 
ADD COLUMN category VARCHAR(30) NOT NULL DEFAULT 'shared_reading' 
COMMENT '類別(shared_reading=共讀計畫, renovation_warrior=裝修小武郎)' 
AFTER report_type;
```

**Unique Key 調整**：`report_id` + `report_type` + `user_id` + `category`

**注意**：現有共讀計畫的 mark 查詢需補上 `->where('category', 'shared_reading')`

---

## 修改檔案清單

| 檔案 | 修改內容 |
|------|---------|
| `routes/web.php` | 新增 1 條推播路由 |
| `app/Http/Controllers/DailyReport/DailyReportViewController.php` | 新增推播方法 + DI |
| `app/Services/Other/SharedReadingReportService.php` | getUserList 擴大範圍、心得分類邏輯、加 category |
| `app/Services/Other/SharedReadingReportExportService.php` | 同上 + Excel 分 Sheet + 推播 |
| `app/Repositories/DailyReport/DailyReportMainRepository.php` | 查詢加入武哥 videoTitle 條件 |
| `app/Repositories/DailyReport/DailyReportSalesRepository.php` | 同上 |
| `app/Repositories/DailyReport/DailyReportForSalesDetailRepository.php` | 同上 |
| `app/Repositories/DailyReport/SharedReadingPlanMarkRepository.php` | 查詢/寫入加 category |
| `app/Models/DailyReport/SharedReadingPlanMark.php` | fillable 加 category |
| `app/Http/Requests/DailyReport/DailyReportSharedReadingReportRequest.php` | mark 加 category 驗證 |
| 語系檔 | 新增武哥匯出 Sheet 設定 |
| Migration | 加 category 欄位 + 改 unique key |

---

## 時程估計

| 項目 | 預估工時 |
|------|---------|
| Service 層修改（分類邏輯 + 人員聯集） | 4h |
| Repository 層（加入 videoTitle 條件） | 2h |
| Excel 分 Sheet 匯出 | 1.5h |
| Migration + Model + Mark 調整 | 1h |
| 推播 API（獨立） | 1.5h |
| 語系檔 | 0.5h |
| 單元測試 | 2h |
| **合計** | **~12.5h** |
