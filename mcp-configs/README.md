# MCP Config 管理

## 環境對照

| 代碼 | URL | 用途 |
|------|-----|------|
| `prod` | `http://mcp.twkd.com:1601` | 正式環境 |
| `beta` | `http://192.168.1.105:1601` | 測試環境 |
| `local` | `http://host.docker.internal:80` | 本地 docker |

## 設計原則

每個 agent 可以混合使用不同環境。宣告方式：

```js
// generate.js 裡的 AGENT_MCP_CONFIGS
bob: {
  profile: 'full',       // 啟用哪些 server
  default: 'local',      // 預設環境
  overrides: {
    'stt-mcp':        'prod',   // stt 走正式
    'image-mcp':      'prod',   // image 走正式
    'wecom-push-mcp': 'prod',   // wecom-push 走正式
    'file-mcp':       'prod',   // file 走正式
  }
}
```

這表示 bob 大部分 server 走本地，但 stt/image/wecom-push/file 因為本地沒有所以走正式。

## 檔案結構

```
mcp-configs/
├── servers.json          # 所有 MCP server 的 path + autoApprove
├── environments/
│   ├── prod.json         # 正式 baseUrl
│   ├── beta.json         # 測試 baseUrl
│   └── local.json        # 本地 baseUrl
├── profiles/
│   ├── full.json         # 完整 server 清單
│   └── minimal.json      # 最小集（核心業務）
├── generate.js           # 生成腳本
└── README.md
```

## 使用方式

```bash
# 生成單一 agent
node mcp-configs/generate.js bob

# 預覽（不寫入）
node mcp-configs/generate.js --dry-run squidward

# 查看完整 JSON 輸出
node mcp-configs/generate.js --show bob

# 生成全部
node mcp-configs/generate.js --all

# 不帶參數看說明
node mcp-configs/generate.js
```

## 常見操作

### 讓 squidward 的 hrs-mcp 切到 beta 測試

```js
squidward: {
  profile: 'full',
  default: 'local',
  overrides: {
    'hrs-mcp': 'beta',  // ← 加這行
  }
}
```

```bash
node mcp-configs/generate.js squidward
```

### 測完了，切回來

把 override 刪掉，重新生成即可。

### 新增 MCP server

1. `servers.json` 加定義（path + autoApprove）
2. 對應 profile（`full.json` 或 `minimal.json`）加入名稱
3. `node mcp-configs/generate.js --all`

### 新增環境

在 `environments/` 建新 JSON：

```json
{
  "baseUrl": "http://new-server:port",
  "token": "your-token"
}
```

## 注意

- workspace 層級的 `.kiro/settings/mcp.json`（你本機 Kiro IDE 用）不受此管理
- 生成後容器需要重啟才會讀到新的 mcp.json
- `autoApprove` 統一在 `servers.json` 定義，各 agent 共用
