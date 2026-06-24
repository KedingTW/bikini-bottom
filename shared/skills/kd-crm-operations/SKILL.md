---
name: kd-crm-operations
description: >
  科定CRM系統操作指引。涵蓋客戶查詢、連絡人查詢、報價單建立、區域業務查詢的完整流程。
  包含 SearchCustomer、SearchCustomerContact、CreateQuote、GetRegionSales 工具使用方式。
  適用於CRM操作、客戶資料查詢、建立報價單相關問題。
---

# 科定 CRM 操作指引

## 適用場景

當需要操作 CRM 系統（查詢客戶、建立報價單、查詢連絡人）時啟用此 skill。

## 可用 CRM 工具

| 工具 | 用途 |
|------|------|
| SearchCustomer | 查詢客戶資料 |
| SearchCustomerContact | 查詢客戶關係連絡人 |
| GetCrmDescription | 查詢CRM物件欄位結構 |
| CreateQuote | 建立報價單 |
| GetRegionSales | 查詢區域負責業務 |

## SearchCustomer 使用方式

### 查詢方式（自動判斷）
- 客戶編號：如 A00123（精確匹配）
- SAP代號：如 TW08971（精確匹配）
- 公司名稱：如 仁普、木根美學（模糊匹配公司全名/簡稱/全名2）

### 回傳重要欄位
- id → 用於 SearchCustomerContact 和 CreateQuote
- 公司全名、簡稱、SAP代號
- 公司電話、傳真、公司地址
- 客戶付款類型（現金客戶/月結客戶）
- **region_name** → 用於 GetRegionSales 和客訴表單
- **target_customer_type** → 用於 GetRegionSales 判斷

## SearchCustomerContact 使用方式

### 必填參數
- account_id：從 SearchCustomer 回傳的 id 取得

### 回傳欄位
- 連絡人編號、姓名、手機號、性別、職稱
- id → 用於 CreateQuote 的 contact_relation_id

## CreateQuote 使用方式

### 必填參數

| 參數 | 說明 | 來源 |
|------|------|------|
| quote_type | 1=房間門, 2=地板, 3=系統櫃, 4=一般 | 依產品判斷 |
| quote_date | 格式 YYYY-MM-DD | 預設今天 |
| account_id | 客戶 ID | SearchCustomer |
| contact_relation_id | 連絡人 ID | SearchCustomerContact |
| payment_type | 付款方式代碼 | 見下方 |
| applicant_name | 業務申請人 | 使用者提供 |

### 付款方式代碼

| 代碼 | 說明 |
|------|------|
| 1 | 現金或匯款 |
| 2 | 月結 |
| 3 | 訂金30%現金或匯款 |
| 4 | 訂金30%月結 |
| 5 | 訂金40%現金或匯款 |
| 6 | 訂金40%月結 |

### 選填參數
- site_address：工地地址
- receiver_name：收貨人（不傳則自動從連絡人帶入）
- receiver_phone：收貨電話（不傳則自動從連絡人帶入）
- receiver_address：收貨地址（不傳則自動從公司地址帶入）

## GetRegionSales 使用方式

### 必填參數
- region_name：從 SearchCustomer 回傳的 region_name（如 TW-B1）
- target_customer_type：從 SearchCustomer 回傳的 target_customer_type

### 判斷邏輯
- 目標客戶類型 = 「經營一」→ 查經營業務（業一）
- 目標客戶類型 = 其他任何值 → 查開發業務（業二）

### 回傳欄位
- sales_name → 負責業務人員姓名
- supervisor_name → 直屬主管姓名

## 標準操作流程

### 建立報價單
```
1. SearchCustomer(keyword="客戶名稱") → 取得 id, 付款類型
2. SearchCustomerContact(account_id=上一步的id) → 取得連絡人 id
3. CreateQuote(quote_type, quote_date, account_id, contact_relation_id, payment_type, applicant_name)
```

### 查詢區域業務（用於客訴）
```
1. SearchCustomer(keyword="客戶名稱") → 取得 region_name, target_customer_type
2. GetRegionSales(region_name, target_customer_type) → 取得 sales_name, supervisor_name
```

## 注意事項

- ⚠️ 付款方式需依客戶付款類型判斷：現金客戶用1/3/5，月結客戶用2/4/6
- ⚠️ 收貨資料不傳時會自動從CRM帶入，通常不需要手動填寫
- ⚠️ quote_date 預設為今天日期
