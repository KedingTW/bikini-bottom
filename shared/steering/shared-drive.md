# 📦 NAS 共享目錄規範

## 路徑對照

| Windows | 容器內 |
|---------|--------|
| `Z:\18_各部門共享區\21_系統開發課\88.BikiniBottom\shared` | `/nas/shared` |

收到 Windows 路徑時，直接轉換使用，不需要問對方。

---

## 目錄結構與用途

```
/nas/shared/
├── workspace/       ← 正式專案工作區（長期保存）
├── drop/            ← 臨時檔案交換（定期清理）
├── docs/            ← 通用知識文件（不屬於特定專案）
├── steering/        ← 共用 steering 檔案（系統用，勿動）
├── reports/         ← [已廢止] 不再使用
├── archive/         ← [已廢止] 不再使用
├── inbox/           ← [已廢止] 不再使用
```

---

## `/nas/shared/workspace/` — 正式專案工作區

### 何時使用
- 任務已經過討論、有明確方向（成案）
- 需要多個 agent 協作的專案產出物
- 需要長期保存的工作成果

### 目錄結構
```
/nas/shared/workspace/{project-name}/
```
- `{project-name}`：英文小寫，用 `-` 連接（例如 `video-digest`、`order-transform`）
- 專案內部結構由負責人自行決定

### 規則
- 新專案由章魚哥（或交辦人指定的負責人）建立目錄
- 專案目錄一旦建立，不隨意刪除或改名
- 每個專案應有 `README.md` 說明用途和負責人

---

## `/nas/shared/drop/` — 臨時檔案交換區

### 何時使用
- 臨時丟給其他 agent 看的檔案
- 尚未歸類、不確定要放哪裡的東西
- 一次性的交換用途

### 檔名格式（強制）
```
<你的名字>_<簡述>_v<版本號>.<副檔名>
```
範例：`bob_api-spec_v1.md`、`patrick_db-schema_v1.sql`

### 版本規則
- 同一份檔案修改後重新放入，版本號必須遞增（v1 → v2 → v3）
- 不要覆蓋舊版本，保留變更歷程
- 取用時認最高版本號

### ⚠️ 重要警告
- `/nas/shared/drop/` 會定期清理，**絕對不要把重要資料只存在這裡**
- 重要檔案一定要保存在自己的工作目錄或 `/nas/shared/workspace/` 下
- 這裡只是「交換」用途，放完就當作會消失
- 不要修改別人放的檔案，要改就複製到自己目錄改
- 可以用子目錄整理相關檔案（例如 `drop/order-transform-review/`）

---

## `/nas/shared/steering/` — 共用 Steering（系統用）

- 由管理員維護，agent 不應修改
- 容器啟動時會 symlink 到各 agent 的 steering 目錄

---

## `/nas/shared/docs/` — 通用知識文件

### 何時使用
- 不屬於特定專案的通用知識、參考資料
- 跨專案共用的技術文件、規範說明
- 團隊共用的學習筆記、操作手冊

### 規則
- 長期保存，不會被清理
- 放的是「知識」而非「專案產出」——專案相關文件放 `workspace/` 下

---

## 已廢止目錄

以下目錄不再使用，保留但不寫入新檔案：
- `reports/` — 報告改放各專案的 workspace 目錄內
- `archive/` — 不再使用獨立歸檔區
- `inbox/` — 不再使用收件匣機制

---

## 判斷流程：檔案該放哪？

```
這個檔案屬於某個已成案的專案嗎？
├── 是 → /nas/shared/workspace/{project-name}/
└── 否 → 這是通用知識/參考文件嗎？
    ├── 是 → /nas/shared/docs/
    └── 否 → 這是臨時交換用的嗎？
        ├── 是 → /nas/shared/drop/
        └── 否 → 先放 drop，等確定歸屬再搬
```
