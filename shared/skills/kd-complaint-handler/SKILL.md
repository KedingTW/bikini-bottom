---
name: kd-complaint-handler
description: >
  科定客訴處理助手。涵蓋客訴建立流程、必填欄位對照、業務人員判斷邏輯、
  客訴查詢與重複檢查、客訴分級說明。
  適用於建立客訴記錄、查詢客訴歷史、處理客訴相關流程。
---

# 科定客訴處理助手

## 適用場景

當需要協助建立客訴記錄、查詢客訴歷史、或處理客訴相關流程時啟用此 skill。

## 客訴建立流程

### 標準步驟

1. **查詢客戶** — `SearchCustomer` 取得公司代號、區域、目標客戶類型
2. **查詢負責業務** — `GetRegionSales` 取得業一/業二處理人員和業三/主管處理人員
3. **重複檢查** — `QueryComplaint`(duplicate_check) 確認是否已有相同客訴
4. **建立客訴** — `CreateComplaint` 填入所有必要欄位

### 必填欄位清單

| 欄位 | 說明 | 來源 |
|------|------|------|
| reporter | 填單人 | 使用者提供 |
| report_type | 回報類型 | 使用者提供 |
| issue_type | 問題類型（產品類型/服務類型） | 使用者提供 |
| complaint_source | 客訴來源 | 使用者提供 |
| company_code | 公司代號 | SearchCustomer |
| company_name | 公司名稱 | SearchCustomer |
| contact_name | 聯絡人 | 使用者提供 |
| contact_gender | 性別 | 使用者提供 |
| contact_phone | 聯絡電話 | 使用者提供 |
| region | 區域 | SearchCustomer (region_name) |
| do_not_disturb | 勿擾申請 | 使用者提供 |
| has_photo | 有照片 | 使用者提供 |
| has_video | 有影片 | 使用者提供 |
| description | 狀況說明 | 使用者提供 |
| has_discount | 折讓 | 使用者提供 |
| handler_level1 | 業一/業二處理人員 | GetRegionSales (sales_name) |
| handler_level3 | 業三/主管處理人員 | GetRegionSales (supervisor_name) |
| complaint_grade | 客訴分級（A/B/C/D/X） | 使用者提供 |
| grade_date | 分級日期 | YYYY-MM-DD |
| responsible_unit | 權責單位 | 使用者提供 |
| responsible_judge_time | 判斷權責處理時間 | YYYY-MM-DD HH:MM:SS |
| type_analysis | 類型分析 | 使用者提供 |
| confidence | AI信心度 | JSON字串 |

### 條件必填

| 條件 | 額外必填欄位 |
|------|-------------|
| issue_type=產品類型 | product_type, defect_type |
| issue_type=服務類型 | service_category |
| service_category=客訴 | complaint_type |
| has_discount=true | discount_reason |

## 業務人員判斷邏輯

使用 `GetRegionSales` 時：
- **region_name**：從 SearchCustomer 回傳的 region_name 取得（如 TW-B1）
- **target_customer_type**：從 SearchCustomer 回傳的 target_customer_type 取得

判斷規則：
- 目標客戶類型 = 「經營一」→ 查經營業務（業一）
- 目標客戶類型 = 其他任何值 → 查開發業務（業二）

回傳對應：
- sales_name → 填入「業一/業二處理人員」(handler_level1)
- supervisor_name → 填入「業三/主管處理人員」(handler_level3)

## 客訴查詢

### 依編號查詢
```
QueryComplaint(query_type="code", complaint_code="202605-00001")
```

### 依公司查歷史
```
QueryComplaint(query_type="history", company_code="TW08971", limit=10)
```

### 重複檢查
```
QueryComplaint(query_type="duplicate_check", order_number="SO12345")
QueryComplaint(query_type="duplicate_check", contact_name="王先生", contact_phone="0912345678")
```

## 客訴分級說明

| 等級 | 說明 |
|------|------|
| A | 最嚴重 |
| B | 嚴重 |
| C | 一般 |
| D | 輕微 |
| X | 特殊 |

## 注意事項

- ⚠️ 建立客訴前務必先做重複檢查
- ⚠️ region 欄位使用 SearchCustomer 回傳的 region_name（如 TW-B1），不是中文地區名
- ⚠️ BD = 加盟招商部，不是國家代碼
