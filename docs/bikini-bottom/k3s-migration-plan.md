# 🏝️ 比奇堡 K3s 遷移規劃

> 從 Docker Compose 遷移到 K3s（輕量 Kubernetes），用 docker compose 經驗帶入說明。

---

## 概念對照表

先建立直覺：K3s 的每個概念都有 docker compose 的對應物。

| Docker Compose | K3s / Kubernetes | 說明 |
|----------------|-----------------|------|
| `docker-compose.yml` | `Deployment` YAML | 定義要跑什麼 container、幾個副本 |
| `services.bob` | `Deployment: bob` | 一個角色 = 一個 Deployment |
| `environment:` | `Secret` + `ConfigMap` | 環境變數拆成機密（token）和設定（channel ID） |
| `.env` 檔案 | `Secret` 物件 | token、密碼等敏感值 |
| `volumes:` | `PersistentVolume` (PV) + `PersistentVolumeClaim` (PVC) | 持久化儲存 |
| `build: .` | Image Registry（GHCR / 本地 registry） | K3s 不在部署時 build，用預先 build 好的 image |
| `restart: unless-stopped` | K3s 內建自癒（Pod 掛了自動重啟） | 比 docker 更強，會自動重新排程 |
| `docker compose up -d` | `kubectl apply -f k3s/` | 部署全部 |
| `docker compose restart bob` | `kubectl rollout restart deployment/bob` | 重啟特定角色 |
| `docker compose logs -f bob` | `kubectl logs -f deployment/bob` | 看 log |
| `docker compose down` | `kubectl delete -f k3s/` | 全部停掉 |
| `extra_hosts` | 不需要（Pod 本身在 host 網路或用 Service） | K3s Pod 預設能連 host |

---

## 為什麼遷移？

### Docker Compose 目前的痛點

1. **NAS 斷線 = 全軍覆沒** — CIFS volume 斷線時，docker compose 沒有自動恢復機制，需手動 `docker compose down -v && up`
2. **滾動更新不方便** — 改 image 後要 `down` + `up`，有短暫停機
3. **資源管控粗糙** — 沒辦法精確限制每個 agent 的 RAM（目前 11 個容器吃同一台機器）
4. **Config 變更要重啟** — volume mount 的 config.toml 改了要手動 restart

### K3s 帶來什麼

1. **自癒** — Pod 掛了自動重啟、NAS 斷線後自動重新掛載嘗試
2. **滾動更新** — 改 image 版本 → `kubectl apply` → 自動一個個換掉，零停機
3. **資源限制** — 每個 Pod 設定 CPU/RAM 上限，避免某個 agent 吃光所有資源
4. **Config 熱更新** — ConfigMap 改了可以觸發 Pod 自動重啟
5. **未來擴展** — 加第二台機器時，K3s 自動把 Pod 分散到多節點

---

## 硬體環境

| 項目 | 規格 |
|------|------|
| OS | Ubuntu Desktop 24.04 LTS |
| RAM | 16 GB（之後升 32 GB） |
| 用途 | 跑 K3s 單節點 cluster |
| 儲存 | NAS Samba 掛載（192.168.1.218） |
| 網路 | 內網，可存取 NAS + MCP Server |

### 資源分配估算（16 GB）

| 元件 | 預估 RAM |
|------|----------|
| Ubuntu Desktop + 系統服務 | ~2 GB |
| K3s control plane | ~512 MB |
| 每個 OpenAB agent（idle） | ~150–250 MB |
| 每個 OpenAB agent（active kiro-cli session） | ~300–500 MB |
| slash-bot (Node.js) | ~100 MB |
| gateway | ~50 MB |
| **合計（11 pods idle）** | **~5–6 GB** |
| **合計（11 pods 全活躍）** | **~8–10 GB** |

16 GB 能跑，但比較緊。建議：
- 設定每個 agent pod 的 memory limit 為 512 MB
- 預留 4 GB 給系統 + K3s
- 升級到 32 GB 後就很寬裕

---

## 架構設計

```
┌─────────────────────────────────────────────────┐
│  Ubuntu Desktop (K3s single-node)               │
│                                                 │
│  ┌─── namespace: bikini-bottom ──────────────┐  │
│  │                                           │  │
│  │  Deployments:                             │  │
│  │    bob, patrick, puff, squidward,         │  │
│  │    sandy, pearl, larry, conch,            │  │
│  │    slash-bot, gateway, wecom-bot          │  │
│  │                                           │  │
│  │  Secrets:                                 │  │
│  │    discord-tokens, kiro-api-keys,         │  │
│  │    github-token, nas-credentials          │  │
│  │                                           │  │
│  │  ConfigMaps:                              │  │
│  │    channel-ids, agent-configs,            │  │
│  │    shared-steering, shared-skills         │  │
│  │                                           │  │
│  │  PersistentVolumes:                       │  │
│  │    nas-shared (CIFS → NAS)                │  │
│  │    agent-home-<name> (hostPath)           │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  /mnt/nas ← mount -t cifs (systemd mount)       │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 遷移步驟

### Phase 1：安裝 K3s（30 分鐘）

```bash
# 安裝 K3s（單節點，不跑 traefik — 我們不需要 ingress）
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik" sh -

# 設定 kubectl（讓一般使用者也能用）
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# 驗證
kubectl get nodes
# → 應該看到一個 Ready 的 node
```

### Phase 2：NAS 掛載（systemd mount 取代 docker volume driver）

```bash
# 安裝 cifs 工具
sudo apt install -y cifs-utils

# 建立 credential 檔（不把密碼寫在 fstab）
sudo tee /etc/nas-credentials <<EOF
username=YOUR_NAS_USER
password=YOUR_NAS_PASSWORD
EOF
sudo chmod 600 /etc/nas-credentials

# 建立掛載點
sudo mkdir -p /mnt/nas

# 寫入 fstab（開機自動掛載）
echo '//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom /mnt/nas cifs credentials=/etc/nas-credentials,file_mode=0777,dir_mode=0777,vers=3.0,iocharset=utf8,echo_interval=10,_netdev,x-systemd.automount 0 0' | sudo tee -a /etc/fstab

# 掛載
sudo mount -a

# 驗證
ls /mnt/nas/shared/
```

重點：用 `x-systemd.automount` 讓 systemd 管理掛載，斷線時自動重試。

### Phase 3：Build Image + 本地 Registry

```bash
# K3s 內建 containerd，可以直接 import image
# 方式一：直接 build + import（簡單，適合單節點）
docker build -t bikini-bottom/agent:latest .
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -

# 方式二：用本地 registry（適合多節點時）
# 暫時不需要，單節點用方式一就好
```

### Phase 4：建立 K8s 資源檔

目錄結構：

```
k3s/
├── namespace.yaml
├── secrets/
│   ├── discord-tokens.yaml
│   ├── kiro-api-keys.yaml
│   ├── github-token.yaml
│   └── nas-credentials.yaml
├── configmaps/
│   ├── channel-ids.yaml
│   └── agent-env.yaml
├── volumes/
│   ├── nas-pv.yaml
│   └── nas-pvc.yaml
├── deployments/
│   ├── bob.yaml
│   ├── patrick.yaml
│   ├── puff.yaml
│   ├── squidward.yaml
│   ├── sandy.yaml
│   ├── pearl.yaml
│   ├── larry.yaml
│   ├── conch.yaml
│   ├── slash-bot.yaml
│   ├── gateway.yaml
│   └── wecom-bot.yaml
└── kustomization.yaml    ← 一鍵部署全部
```

### Phase 5：部署

```bash
# 部署全部
kubectl apply -k k3s/

# 看狀態（等同 docker ps）
kubectl get pods -n bikini-bottom

# 看特定 agent log
kubectl logs -f deployment/bob -n bikini-bottom

# 重啟某個 agent（等同 docker compose restart bob）
kubectl rollout restart deployment/bob -n bikini-bottom
```

---

## 常用操作對照

| 我要… | Docker Compose | K3s |
|--------|---------------|-----|
| 部署全部 | `docker compose up -d --build` | `kubectl apply -k k3s/` |
| 停全部 | `docker compose down` | `kubectl delete -k k3s/` |
| 重啟一個 | `docker compose restart bob` | `kubectl rollout restart deploy/bob -n bikini-bottom` |
| 看 log | `docker compose logs -f bob` | `kubectl logs -f deploy/bob -n bikini-bottom` |
| 進容器 | `docker exec -it bob bash` | `kubectl exec -it deploy/bob -n bikini-bottom -- bash` |
| 改環境變數 | 編輯 .env → restart | 編輯 Secret → rollout restart |
| 更新 image | `docker compose build && up -d` | `docker build` → `k3s ctr import` → `kubectl rollout restart` |
| 看資源用量 | `docker stats` | `kubectl top pods -n bikini-bottom` |

---

## 遷移時程

| 階段 | 預計時間 | 內容 |
|------|----------|------|
| Day 1 | 2 小時 | 裝 Ubuntu + K3s + NAS 掛載 |
| Day 1 | 1 小時 | Build image + 建立 namespace/secrets/configmaps |
| Day 1 | 2 小時 | 寫 deployment YAML（先上 bob 一個測試） |
| Day 2 | 1 小時 | bob 驗證通過 → 部署全部角色 |
| Day 2 | 1 小時 | 驗證 Discord mention 回應 + MCP 連線 |
| Day 2 | 30 分鐘 | 切換 DNS/IP（如有需要）+ 關閉舊 docker compose |

**總計：約 1.5 天**

---

## 風險與緩解

| 風險 | 影響 | 緩解方式 |
|------|------|----------|
| K3s 學習曲線 | 部署速度慢 | 本文件 + 操作對照表 + 我可以生成所有 YAML |
| NAS 掛載斷線 | Agent 讀不到 projects | systemd automount 自動重試 + liveness probe |
| 16 GB RAM 不夠 | OOM kill | 設 memory limit 512MB/pod + 先跑 8 個核心 agent |
| Image build 流程改變 | CI/CD 要調 | 先手動 build+import，之後再加 GitHub Actions |
| 舊 docker compose 環境 | 要保留嗎？ | 建議保留 1 週作為 rollback 方案 |

---

## 下一步

1. ✅ 本文件規劃完成
2. ⬜ 等收到新桌機 → 安裝 Ubuntu + K3s
3. ⬜ 我生成完整的 `k3s/` 目錄下所有 YAML 檔案
4. ⬜ 先上 bob 單一 agent 做 smoke test
5. ⬜ 全部角色部署 + 驗證

要我現在就開始生成 `k3s/` 目錄下的 YAML 檔案嗎？還是等桌機到了再來？
