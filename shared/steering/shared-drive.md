# 📦 共用儲存與家目錄規範

## 路徑對照

| Windows | 容器內 |
|---------|--------|
| `Z:\18_各部門共享區\21_系統開發課\88.BikiniBottom\shared` | `/shared` |

收到 Windows 路徑時，直接轉換使用，不需要問對方。

---

## `/home/agent/` — 個人家目錄（私人空間）

### 說明
你的家目錄是你私人的工作空間，沒有人會來看。你應該自己管理好裡面的內容。

### 目錄結構
```
~/
├── _projects.md              ← 經手專案總覽（自行維護）
├── workspace/                ← 工作區（掛載自 kd-dev）
│   └── projects/
│       └── xxx-project/
│           └── _status.md    ← 該專案進度
├── .kiro/                    ← 系統設定（勿亂動）
│   ├── steering/             ← 人設、規則、記憶
│   ├── context/              ← 觸發式上下文（可自行新增 .md）
│   ├── settings/             ← mcp.json, cli.json
│   └── skills/               ← 技能（symlink，唯讀）
├── .openab/                  ← 框架資料
│   ├── cronjob.toml          ← 排程任務（可自行設定）
│   └── thread_map.json       ← 框架自動管理
└── ...
```

### 規則
- `~/workspace/projects/` 放你自己正在處理的專案草稿、工作檔
- 要交付給別人的東西放 `/shared/workspace/` 或 `/shared/drop/`
- `~/_projects.md` 記錄所有經手的專案清單
- 各專案目錄內用 `_status.md` 記錄進度
- 其他 `_xxx.md` 用於記錄個人計畫、待辦事項等

### 與 /shared 的差別
| | ~/（家目錄） | /shared/ |
|--|-------------|----------|
| 誰能看 | 只有你自己 | 所有角色 + 人類 |
| 用途 | 草稿、進行中的工作、私人筆記 | 交付物、協作檔案 |
| 生命週期 | 你自己管理 | 按專案/drop 規則管理 |

---

## `/shared/` — 共用目錄結構與用途

```
/shared/
├── workspace/       ← 正式專案工作區（長期保存）
├── drop/            ← 臨時檔案交換（定期清理）
├── docs/            ← 通用知識文件（不屬於特定專案）
├── steering/        ← 共用 steering 檔案（系統用，勿動）
├── reports/         ← [已廢止] 不再使用
├── archive/         ← [已廢止] 不再使用
├── inbox/           ← [已廢止] 不再使用
```

---

## `/shared/workspace/` — 正式專案工作區

### 何時使用
- 任務已經過討論、有明確方向（成案）
- 需要多個 agent 協作的專案產出物
- 需要長期保存的工作成果

### 目錄結構
```
/shared/workspace/{project-name}/
```
- `{project-name}`：英文小寫，用 `-` 連接（例如 `video-digest`、`order-transform`）
- 專案內部結構由負責人自行決定

### 規則
- 新專案由章魚哥（或交辦人指定的負責人）建立目錄
- 專案目錄一旦建立，不隨意刪除或改名
- 每個專案應有 `README.md` 說明用途和負責人

---

## `/shared/drop/` — 臨時檔案交換區

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
- `/shared/drop/` 會定期清理，**絕對不要把重要資料只存在這裡**
- 重要檔案一定要保存在自己的工作目錄或 `/shared/workspace/` 下
- 這裡只是「交換」用途，放完就當作會消失
- 不要修改別人放的檔案，要改就複製到自己目錄改
- 可以用子目錄整理相關檔案（例如 `drop/order-transform-review/`）

---

## `/shared/steering/` — 共用 Steering（系統用）

- 由管理員維護，agent 不應修改
- 容器啟動時會 symlink 到各 agent 的 steering 目錄

---

## `/shared/docs/` — 通用知識文件

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
這個檔案是我自己的草稿/進行中的工作嗎？
├── 是 → ~/workspace/projects/{project-name}/
└── 否 → 這個檔案屬於某個已成案的專案嗎？
    ├── 是 → /shared/workspace/{project-name}/
    └── 否 → 這是通用知識/參考文件嗎？
        ├── 是 → /shared/docs/
        └── 否 → 這是臨時交換用的嗎？
            ├── 是 → /shared/drop/
            └── 否 → 先放 ~/workspace/projects/ 自己管理
```
