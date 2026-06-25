---
inclusion: manual
---
# 基礎設施操作規範

## 環境架構

- 所有 agent 角色和 admin dashboard 都跑在 **k3s**（輕量 Kubernetes）
- 部署 manifests 在 `k3s/deployments/` 目錄
- **不要用 Docker 直接跑服務**，Docker 只用於 build image
- 如果看到 Docker 容器佔用了 k8s NodePort，那是殘留，應該停掉而非修它

## 操作原則

1. **先讀 manifest 再動手** — 任何服務出問題，先去 `k3s/deployments/` 看它的 yaml 定義
2. **不要自行創建 Docker 容器來替代 k8s 服務**
3. **不要刪除 k8s deployment/service** — 除非要永久移除該服務
4. **修復順序：確認問題 → 提出方案 → 等用戶確認 → 執行**
5. **不要連續嘗試多種方法** — 一次失敗就停下來，跟用戶說清楚狀況再繼續

## 重啟/恢復

- 重新部署服務：`kubectl apply -f k3s/deployments/<service>.yaml`
- 重啟單一服務：`kubectl rollout restart deployment <name> -n bikini-bottom`
- 重啟所有服務需要用戶明確同意

## Port 對照

| 服務 | NodePort |
|------|----------|
| admin dashboard | 30080 |
| mcp-server (Docker) | 1601 (HTTP), 1602 (HTTPS) |
| mcp-redis (Docker) | 1603 |

## 注意事項

- 這是正式環境，任何可能中斷服務的操作都要先告知用戶
- `docker ps` 看到的容器不代表是主要服務，k8s pods 才是
- 機器內網 IP 可能變動（DHCP），k3s 重啟可修復相關路由問題
