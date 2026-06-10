# 新增 Bot SOP — 科定WeCom

> ⚠️ **狀態：暫停**
> WeCom 缺乏表情反應機制，使用者體驗不佳，已改用 DC 方式。
> 此文件保留作為未來重啟參考。

---

## 架構

```
WeCom 應用 ──HTTPS──▶ Zeabur gateway ◀══wss══ 地端 K3s wecom-bot ──▶ MCP
```

## 完整部署文件

參考 [wecom-zeabur-setup.md](./wecom-zeabur-setup.md)

## 管理工具

參考 [services/zeabur-gateway/README.md](../services/zeabur-gateway/README.md)

## 現有 Bot

| Bot | Agent 路徑 | Zeabur Service | 狀態 |
|-----|-----------|----------------|------|
| 下單小幫手 | `agents/keding-wecom/order-transform/` | `gateway-order-transform` | ⏸ 暫停 |
