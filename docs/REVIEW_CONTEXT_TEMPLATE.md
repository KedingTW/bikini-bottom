# REVIEW_CONTEXT.md 範本

> 將此檔案放在各 repo 的 `.github/REVIEW_CONTEXT.md`，泡芙阿姨會在審閱時自動讀取。
> 如果 repo 沒有此檔案，泡芙阿姨只使用通用審查規則。

---

以下為範本內容，請依專案實際情況修改：

```markdown
# Review Context

## 技術棧
- （例如：PHP 8.2 + Laravel 10）
- （例如：Python 3.11 + FastAPI）
- （例如：Vue 3 + Composition API + TypeScript）

## 分層架構
- （例如：Controller → Service → Repository → Model）
- （例如：Router → Service → CRUD → Schema）
- （例如：Component → Composable → Store → API Module）

## 命名慣例
- （例如：PHP 變數/函式 camelCase，資料庫欄位 snake_case）
- （例如：Python 全部 snake_case，類別 PascalCase）

## 專案特殊規則
- （例如：所有 API response 必須經過 Resource/Schema 轉換）
- （例如：禁止在 Controller/Router 直接操作資料庫）
- （例如：所有 composable 必須以 use 開頭）

## 忽略項目
- （例如：migrations/ 目錄不需要 review）
- （例如：自動生成的檔案不需要 review）
```
