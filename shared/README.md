# 📦 共享檔案交換區

掛載路徑：容器內 `/shared`

## 結構

```
/shared/
├── README.md       # 本說明（唯讀參考）
└── drop/           # 檔案交換區（扁平，每日清空）
```

## 規則

### 檔名格式（強制）

```
<寄件人>_<簡述>_v<版本號>.<副檔名>
```

範例：
- `bob_api-spec_v1.md`
- `bob_api-spec_v2.md`（修改後重新放入）
- `sandy_analysis-report_v1.pdf`
- `squidward_sprint-plan_v3.md`

### 版本控制

- 同一份檔案經過編修後重新放入，**必須遞增版本號**
- 不要覆蓋舊版本，讓收件人能看到變更歷程
- 收件人取用時，取最高版本號的檔案

### 使用流程

1. 想讓對方看到檔案 → 複製到 `/shared/drop/`
2. 在 Discord 告知對方：「檔案放在共享區了」
3. 收件人從 `/shared/drop/` 讀取或複製到自己的工作目錄

### 清理機制

- 每日自動清空 `/shared/drop/` 內所有檔案
- 重要檔案請自行備份到自己的工作目錄，不要只存在這裡
- 這裡是「交換」用，不是「儲存」用

<!-- TODO: 設定 cron job 每日清空 /shared/drop/（保留 .gitkeep） -->
<!-- 建議指令: find /path/to/shared/drop -type f ! -name '.gitkeep' -delete -->
