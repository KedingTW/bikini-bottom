# 新增 Bot SOP — 索引

建立新 bot 前，先確認要加入哪個伺服器：

| 伺服器 | 用途 | 使用者 | SOP 文件 |
|--------|------|--------|---------|
| 比奇堡 (DC) | AI 開發團隊（通用 agent） | 開發者 | [bot-setup-sop-bikini-bottom.md](./bot-setup-sop-bikini-bottom.md) |
| 科定AI服務 (DC) | 業務專用 bot（單一職責） | 同事 | [bot-setup-sop-keding-dc.md](./bot-setup-sop-keding-dc.md) |
| 科定WeCom | WeCom bot（暫停） | 同事 | [bot-setup-sop-keding-wecom.md](./bot-setup-sop-keding-wecom.md) |

---

## 三組差異總覽

| 項目 | 比奇堡 | 科定DC | 科定WeCom |
|------|--------|--------|-----------|
| 平台 | Discord | Discord | WeCom |
| Entrypoint | `entrypoint-wrapper.sh` | `entrypoint-minimal.sh` | `entrypoint-minimal.sh` |
| NAS | 需要 | 不需要 | 不需要 |
| Shared steering/skills | 需要 | 不需要 | 不需要 |
| Image | `bikini-bottom/agent:latest` | 同（未來可能獨立） | 同 |
| agents 目錄 | `agents/bikini-bottom/`（待搬） | `agents/keding-dc/` | `agents/keding-wecom/` |
| K3s secret | `discord-tokens` + `kiro-api-keys` | `keding-dc-secrets` | — |
| Bot 個性 | 有（角色扮演） | 無（專業簡短） | 無 |
| 權限控制 | 無 | 有（管理員 vs 同事） | 有 |
| 狀態 | ✅ 運作中 | ✅ 運作中 | ⏸ 暫停 |
