# 知識庫與規則載入

## 強制讀取規則（不可跳過）

收到訂單訊息時，**必須先用 read tool 讀取 `~/memory/order-rules.md`**，讀到完整規則後再進行轉換。
沒讀規則就直接回答 = 違規。每個新討論串的第一次轉換都要讀。

## 規則更新流程

- 馥寧/米哥糾正 → 先記錄到 `~/memory/rules.md`（待確認）
- 馥寧/米哥確認 → 用 `fs_append` 寫入 `~/memory/order-rules.md`（正本）
