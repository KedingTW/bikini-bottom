---
inclusion: manual
---
# 基礎設施操作規範

## 環境架構

- 所有 agent 角色和 admin dashboard 都跑在 **k3s**（輕量 Kubernetes）
- 部署 manifests 在 `k3s/deployments/` 目錄
- **不要用 Docker 直接跑服務**，Docker 只用於 build image
- 如果看到 Docker 容器佔用了 k8s NodePort，那是殘留，應該停掉而非修它
- **開發機 = K3s 主機** — 這台機器同時是開發環境和 K3s cluster 所在機器，`kubectl` 可直接操作，不需要 SSH 到遠端
- 排程任務使用 `/etc/cron.d/` 或 `crontab`，不要用 `at`

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

## NAS 掛載規則

Host 上有三個 NAS 掛載點，不要搞混：

| 掛載點 | 用途 | 對應 NAS 路徑 |
|--------|------|---------------|
| `/mnt/kd-dev` | 比奇堡 (bikini-bottom) 專用 | 88.BikiniBottom |
| `/mnt/kd-dc` | keding-dc 專用 | keding-dc 對應目錄 |
| `/mnt/kd-share` | 頂層公司共用目錄 | kd共用 根目錄 |

規則：
- **`/mnt/nas` 已廢棄**，不再使用。不要在任何配置中引用它。
- 比奇堡角色統一用 hostPath 掛載 `/mnt/kd-dev` 下的子目錄，不使用 PVC。
- 比奇堡角色不需要掛 `/mnt/kd-share`。
- keding-dc 角色用 `/mnt/kd-dc` 和 `/mnt/kd-share`。

## 切換 Kiro API Key（換帳號）

當用戶說「換 key」「重啟 pod」時，代表 `.env` 已改好，執行以下步驟：

1. 讀 `.env` 中啟用的 `KIRO_API_KEY` 值（`grep '^KIRO_API_KEY=' .env`）
2. 更新 K8s Secret：
   ```bash
   NEW_KEY=$(grep '^KIRO_API_KEY=' .env | head -1 | sed 's/KIRO_API_KEY=\([^ ]*\).*/\1/')
   kubectl create secret generic kiro-api-keys -n bikini-bottom \
     --from-literal=BOB="$NEW_KEY" --from-literal=CONCH="$NEW_KEY" \
     --from-literal=GARY="$NEW_KEY" --from-literal=KAREN="$NEW_KEY" \
     --from-literal=LARRY="$NEW_KEY" --from-literal=MERMAID_MAN="$NEW_KEY" \
     --from-literal=PATRICK="$NEW_KEY" --from-literal=PEARL="$NEW_KEY" \
     --from-literal=PUFF="$NEW_KEY" --from-literal=SANDY="$NEW_KEY" \
     --from-literal=SQUIDWARD="$NEW_KEY" --from-literal=WECOM_BOT="$NEW_KEY" \
     --from-literal=WECOM_BOT_ORDER_TRANSFORM="$NEW_KEY" \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
3. 重啟 pod：`kubectl rollout restart deployment -n bikini-bottom`
4. 等 30 秒後驗證：`kubectl exec -n bikini-bottom deploy/bob -- sh -c 'echo $KIRO_API_KEY' | cut -c1-8`
5. 回報結果

**重要：**
- `.env` 是人類手動改好的，不要動它
- Pod 的 `KIRO_API_KEY` 來自 K8s Secret `kiro-api-keys`，不是直接讀 `.env`
- 改 `.env` 不會自動生效，必須更新 Secret + 重啟 pod
- 帳號命名：Bikini-Bottom-1 / Bikini-Bottom-2 / Bikini-Bottom-3（行尾註解辨識）
- 腳本位置：`scripts/switch-kiro-account.sh`

## 注意事項

- 這是正式環境，任何可能中斷服務的操作都要先告知用戶
- `docker ps` 看到的容器不代表是主要服務，k8s pods 才是
- 機器內網 IP 可能變動（DHCP），k3s 重啟可修復相關路由問題
