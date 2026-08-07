# 📦 共用儲存規範（比奇堡）

## 掛載路徑

| 容器內路徑 | 權限 | 用途 |
|-----------|------|------|
| `/mnt/kd-dev` | **可讀寫** | 比奇堡團隊專屬工作區 |

## 目錄結構

```
/mnt/kd-dev/
├── shared/
│   ├── workspace/       ← 正式專案工作區（長期保存）
│   ├── drop/            ← 臨時檔案交換（定期清理）
│   └── docs/            ← 通用知識文件
└── agents/              ← 各 agent 的 projects 目錄
```

---

## `/mnt/kd-dev/shared/workspace/` — 正式專案工作區

### 何時使用
- 任務已成案，有明確方向
- 需要多個 agent 協作的專案產出物
- 需要長期保存的工作成果

### 目錄結構
```
/mnt/kd-dev/shared/workspace/{project-name}/
```
- `{project-name}`：英文小寫，用 `-` 連接（例如 `video-digest`、`order-transform`）
- 新專案由章魚哥或交辦人指定的負責人建立

---

## `/mnt/kd-dev/shared/drop/` — 臨時檔案交換區

### 檔名格式（強制）
```
<你的名字>_<簡述>_v<版本號>.<副檔名>
```
範例：`bob_api-spec_v1.md`、`patrick_db-schema_v1.sql`

### 規則
- 同一份檔案修改後版本號遞增（v1 → v2 → v3）
- 不要覆蓋舊版本
- **此目錄會定期清理，不要存放重要資料**
- 不要修改別人放的檔案

---

## `/mnt/kd-dev/shared/docs/` — 通用知識文件

- 不屬於特定專案的通用知識、參考資料
- 長期保存，不會被清理

---

## 判斷流程：檔案該放哪？

```
屬於某個已成案的專案？
├── 是 → /mnt/kd-dev/shared/workspace/{project-name}/
└── 否 → 通用知識/參考文件？
    ├── 是 → /mnt/kd-dev/shared/docs/
    └── 否 → /mnt/kd-dev/shared/drop/
```
