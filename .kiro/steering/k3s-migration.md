---
inclusion: manual
---

# K3s 遷移作業指引

> 本文件是 Kiro IDE 在新桌機上協助使用者完成 K3s 遷移的完整上下文。
> 使用者說「執行 K3s 設置」或類似指令時，按照本文件流程引導。

## 背景

比奇堡 AI 開發團隊（11 個 OpenAB agent）正在從 Docker Compose（Windows WSL2）遷移到 K3s（Ubuntu Desktop 單節點）。

### 目前架構（舊）
- 執行在 Windows + Docker Desktop (WSL2)
- `docker-compose.yml` 管理 11 個 OpenAB agent 容器
- NAS 掛載用 docker CIFS volume driver
- 環境變數放在 `.env`

### 目標架構（新）
- 執行在 Ubuntu Desktop 24.04（16GB RAM，之後升 32GB）
- K3s 單節點 cluster
- NAS 掛載用 systemd automount（`/mnt/nas`）
- 機密值放在 K8s Secret，設定放在 ConfigMap
- 所有 Deployment YAML 在 `k3s/` 目錄

## 相關文件

- `docs/k3s-migration-plan.md` — 遷移規劃（架構設計、時程、風險）
- `docs/k3s-operations-guide.md` — 維運指南（日常操作、問題排除）
- `scripts/k3s-setup.sh` — 自動化安裝腳本
- `scripts/k3s-cutover.sh` — 切換腳本
- `k3s/` — 完整 K8s 資源定義

## 設置流程（在新桌機上執行）

### Phase 0：前置確認

確認以下已完成：
- [ ] Ubuntu Desktop 24.04 已安裝
- [ ] 網路正常（能上網、能 ping 192.168.1.218 NAS）
- [ ] Kiro IDE 已安裝
- [ ] 本 repo 已 clone 並切換到 `feat/k3s-migration` 分支
- [ ] 從舊機複製了 `.env` 檔案（包含所有 token 和 key）

### Phase 1：系統安裝（腳本自動化）

執行 `scripts/k3s-setup.sh`，會自動完成：
1. 安裝 Docker（build image 用，K3s 本身不需要 Docker）
2. 安裝 K3s（單節點，停用 traefik）
3. 設定 kubectl 權限
4. 安裝 cifs-utils
5. 建立 NAS credential 檔案（需使用者輸入帳密）
6. 設定 `/mnt/nas` 的 fstab + systemd automount
7. 掛載 NAS 並驗證

### Phase 2：Build Image + 匯入 K3s

```bash
# Build agent image
docker build -t bikini-bottom/agent:latest .

# 匯入到 K3s 的 containerd
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -

```

### Phase 3：建立 K8s 資源

```bash
# 從 .env 生成 Secrets
bash scripts/k3s-create-secrets.sh

# 部署全部（replicas=0，先不啟動）
kubectl apply -k k3s/
```

### Phase 4：驗證（不啟動服務）

```bash
# 確認所有資源建立成功
kubectl get all -n bikini-bottom

# 應該看到 Deployment 都是 0/0 READY
# 確認 PV/PVC bound
kubectl get pv,pvc -n bikini-bottom
```

### Phase 5：切換（停機 5~10 分鐘）

```bash
# ① 使用者在舊機執行：docker compose down
# ② 在新機執行切換腳本：
bash scripts/k3s-cutover.sh

# 腳本會：
# - scale 所有 deployment replicas=1
# - 等待所有 Pod Running
# - 顯示狀態
```

### Phase 6：驗證服務恢復

- 在 Discord mention 任一 bot 確認回應
- 檢查 `kubectl logs` 確認無錯誤
- 確認 NAS 檔案可讀寫

### Rollback（如果失敗）

```bash
# 新機：停掉所有 Pod
kubectl scale deployment --all -n bikini-bottom --replicas=0

# 舊機：恢復
docker compose up -d
```

## 重要注意事項

- Discord Bot Token 是獨占的，新舊不能同時跑
- `.env` 裡的值跟舊機完全一樣，直接複製
- NAS IP: 192.168.1.218，路徑: `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom`
- MCP Server 在 host.docker.internal:80（K3s Pod 用 hostNetwork 或 node IP 連）
- 每個 agent Pod 的 memory limit 建議 512Mi（16GB RAM 環境）

## Agent 列表

| 角色 | 容器名/Deployment 名 | 類型 |
|------|---------------------|------|
| 海綿寶寶 | bob | OpenAB agent |
| 派大星 | patrick | OpenAB agent |
| 泡芙老師 | puff | OpenAB agent |
| 章魚哥 | squidward | OpenAB agent |
| 珊迪 | sandy | OpenAB agent |
| 珍珍 | pearl | OpenAB agent |
| 蝦霸 | larry | OpenAB agent |
| 神奇海螺 | conch | OpenAB agent |
| Gateway | gateway | WeCom Gateway |
