# 排程任務設定（Cronjob）

## 唯一正確做法

排程任務**只能**透過編輯 `~/.openab/cronjob.toml` 設定。OpenAB 內建 scheduler 每分鐘檢查一次，檔案修改後自動 hot-reload，不需重啟。

**禁止：**
- ❌ 安裝 cron、crontab、systemd、daemon、at、或任何 Linux 排程工具
- ❌ 使用 `crontab -e` 或任何系統層級排程
- ❌ 建立 shell script 搭配 sleep loop
- ❌ 使用 nohup、screen、tmux 等背景執行方式
- ❌ 使用 GitHub Actions 或 K8s CronJob（簡單排程不需要）

**正確做法：** 直接編輯 `~/.openab/cronjob.toml`，寫入 `[[jobs]]` 區塊即可。

---

## cronjob.toml 格式

```toml
[[jobs]]
schedule = "0 9 * * 1-5"               # 必填：5-field POSIX cron（分 時 日 月 週）
channel = "1492090122257170526"         # 必填：Discord channel ID（數字字串，不支援 ${} 變數）
message = "要執行的任務描述"              # 必填：發送給自己的 prompt
sender_name = "DailyOps"               # 選填，預設 "openab-cron"
timezone = "Asia/Taipei"               # 選填，預設 "UTC"
thread_id = "1234567890"               # 選填：發到指定 thread
platform = "discord"                   # 選填，預設 "discord"
enabled = true                         # 選填，預設 true（設 false 暫停不刪除）
```

## Cron 表達式

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-7, 0 和 7 = 週日)
│ │ │ │ │
* * * * *
```

支援 `Mon-Fri` 名稱寫法，但不可混用數字和名稱（如 `1,Mon` 不合法）。

## 常用 Channel ID

| 頻道 | Channel ID |
|------|-----------|
| 蟹堡王 | 1492090122257170526 |
| 廣場 | 1503940169252999198 |
| 會議室 | 1503703338800382002 |

## 重要行為

- **Overlap protection**：前一次執行還在跑時，下一次會被跳過
- **Hot-reload**：修改檔案後 ≤1 分鐘自動生效，不需重啟容器
- **channel 不支援 `${...}` 環境變數**，必須直接寫 channel ID 數字字串
- 一次性任務執行完後記得刪除該 `[[jobs]]` 段落
- 檔案不存在或 TOML 語法錯誤時，只影響動態任務，不影響 config.toml 的 baseline jobs
