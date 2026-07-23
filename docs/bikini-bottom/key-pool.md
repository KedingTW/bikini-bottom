# Key Pool — Kiro API Key 自動輪替機制

## 概述

Key Pool 讓所有 agent pod 自動共用和輪替 Kiro API key，不再需要人工換 key。

**策略**：Sequential Drain — 集中用滿一把再換下一把，減少月費。

---

## 架構

```
Agent Pod                          Admin Pod
┌─────────────────┐               ┌──────────────────────┐
│ kiro-key-wrap   │──── pick ────▶│ POST /api/key-pool/  │
│   ↓             │               │   pick / mark / state│
│ kiro-cli        │               │                      │
│   (with key)    │               │ MySQL: key_pool 表   │
│   ↓             │               │                      │
│ stderr monitor  │──── mark ────▶│ Usage 排程（每小時） │
└─────────────────┘               └──────────────────────┘
```

---

## 運作流程

### 正常路徑（每個 session）

1. Agent session 啟動 → `kiro-key-wrap` 向 admin `POST /pick`
2. Admin 回傳 priority 最高的可用 key
3. Wrap 注入 `KIRO_API_KEY` env，spawn `kiro-cli`
4. Session 結束

### 耗盡偵測

- **即時**：wrap 監聽 kiro-cli stderr，比對 rate-limit regex → `POST /mark`
- **排程**：admin 每小時查所有 key 用量，≥ 100% 自動 mark exhausted

### 自動恢復

- Mark 時設 `exhausted_until` = 下個月 1 號 00:00（台灣時間）
- Pick SQL 過濾：`exhausted_until IS NULL OR exhausted_until < NOW()`
- 到期自動恢復，無需人工

---

## API 端點

| 方法 | 路徑 | 用途 |
|------|------|------|
| POST | `/api/key-pool/pick` | 取得一把可用 key |
| POST | `/api/key-pool/mark` | 標記 key 耗盡 |
| GET | `/api/key-pool/state` | 查看 pool 狀態 |
| POST | `/api/key-pool/check-usage` | 手動觸發用量查詢 |

---

## 告警

條件成立時發送 Discord 通知：

| 條件 | 訊息 |
|------|------|
| Current key ≥ 80% 且無備援 key | ⚠️ 最後一把快用完，無備援 |
| Current key ≥ 100% | 🚨 已超額使用中 |

---

## 管理操作

### 新增 key

```sql
INSERT INTO key_pool (key_name, key_value, priority, note)
VALUES ('POOL_04', 'kiro_xxxxx', 4, '備援 3 - account@example.com');
```

### 手動解除耗盡

```sql
UPDATE key_pool SET exhausted_until = NULL, exhausted_reason = NULL
WHERE key_name = 'POOL_01';
```

### 停用 key

```sql
UPDATE key_pool SET enabled = 0 WHERE key_name = 'POOL_02';
```

### 查看狀態

```bash
curl http://admin:8501/api/key-pool/state | jq
```

### 手動觸發用量查詢

```bash
curl -X POST http://admin:8501/api/key-pool/check-usage | jq
```

---

## 資料表

| 表 | 用途 | 保留期限 |
|----|------|----------|
| `key_pool` | Key 池主表 | 永久 |
| `key_usage_history` | 用量歷史 | 建議 90 天清理 |
| `pick_log` | Pick 紀錄 | 建議 90 天清理 |
| `exhausted_log` | 耗盡事件 | 永久 |

---

## 環境變數

### Agent Pod

| 變數 | 說明 |
|------|------|
| `KEY_POOL_URL` | Admin key-pool API base URL |
| `AGENT_NAME` | Agent 名稱（已有） |

### Admin Pod

| 變數 | 說明 | 預設 |
|------|------|------|
| `KEY_POOL_ALERT_CHANNEL` | 告警 Discord 頻道 | `1493802266296188988` |
| `KEY_POOL_ALERT_THRESHOLD` | 用量告警百分比 | `80` |
| `KEY_POOL_ALERT_REMAINING` | 剩餘 key 數告警閾值 | `1` |
| `KEY_POOL_USAGE_INTERVAL` | 用量查詢間隔（小時） | `1` |

---

## 回滾

如果出問題：
1. Agent config.toml 改回 `command = "kiro-cli"`
2. Deployment YAML 恢復 `KIRO_API_KEY` env
3. Rollout restart agent pod
