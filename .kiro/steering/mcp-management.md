---
inclusion: manual
---

# MCP 環境管理指引

## 概念

每個 agent 的 `.kiro/settings/mcp.json` 由 `mcp-configs/generate.js` 自動產生。
使用者只需描述需求，agent 負責修改設定並執行生成。

## 環境對照

| 代碼 | URL | 用途 |
|------|-----|------|
| `prod` | `http://mcp.twkd.com:1601` | 正式環境 |
| `beta` | `http://192.168.1.105:1601` | 測試環境 |
| `local` | `http://host.docker.internal:80` | 本地 docker 內 |

## 操作流程

1. 修改 `mcp-configs/generate.js` 中的 `AGENT_MCP_CONFIGS`
2. 執行 `node mcp-configs/generate.js <agent名稱>` 或 `--all`
3. 提醒使用者重啟對應容器

## 設定格式

```js
agentName: {
  profile: 'full',        // 啟用的 server 清單（full / minimal）
  default: 'local',       // 預設環境
  overrides: {
    'server-name': 'prod',  // 個別 server 指向不同環境
  }
}
```

## 新增 MCP Server 流程

1. `mcp-configs/servers.json` 加入 server 定義（path + autoApprove）
2. `mcp-configs/profiles/*.json` 加入 server 名稱
3. 執行 `node mcp-configs/generate.js --all`

## 注意

- workspace 層級 `.kiro/settings/mcp.json`（Kiro IDE 本機用）不受此管理，需手動維護
- 生成後容器需重啟才生效
