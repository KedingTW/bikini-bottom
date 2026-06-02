# 🚀 比奇堡 K3s 遷移規劃

> 建立日期：2026-06-02
> 狀態：規劃中
> 目標：從 Windows Docker Compose 遷移至 Linux + K3s + Helm

---

## 背景與動機

### 目前架構
- Windows 主機 + Docker Desktop（WSL2 backend）
- `docker-compose.yml` 管理所有 agent + 服務
- NAS 透過 CIFS volume 掛載
- 小蝸（slash-bot）透過 docker.sock 管理容器

### 痛點
1. **NAS CIFS 斷線** — WSL2 kernel 的 CIFS 實作不完整，不支援 `soft`/`reconnect`，斷線後 volume stale，需手動 `compose down && up`
2. **無法自動恢復** — 小蝸容器內無 docker CLI，無法執行 compose 操作
3. **Windows 不穩定** — 休眠/更新/重啟都會導致全員斷線
4. **密鑰集中** — 所有 token 在同一個 `.env` 檔案
5. **更新笨重** — 改任何設定都需要全員重建

### 遷移後的好處
| 類別 | 好處 |
|---|---|
| 穩定性 | Linux 原生 NFS mount（`soft,reconnect`），斷線自動恢復 |
| 自動修復 | K8s 偵測 Pod 異常自動重啟，不需人工介入 |
| 獨立生命週期 | 重啟 bob 不影響 patrick |
| 版本更新 | `helm upgrade` 一行搞定，滾動更新不斷線 |
| 資源管理 | 每個 agent 可設 CPU/RAM 上限 |
| 密鑰隔離 | 每個 agent 獨立 Kubernetes Secret |
| 監控 | K8s 原生健康檢查 + 事件日誌 |
| 小蝸升級 | 用 K8s Python client 操作，不再需要 docker.sock |

---

## 目標架構

```
Linux Server (Ubuntu 24.04 LTS)
├── K3s（單節點）
│   ├── Namespace: bikini-bottom
│   │   ├── Deployment: bob        (OpenAB Helm)
│   │   ├── Deployment: patrick    (OpenAB Helm)
│   │   ├── Deployment: squidward  (OpenAB Helm)
│   │   ├── Deployment: sandy      (OpenAB Helm)
│   │   ├── Deployment: puff       (OpenAB Helm)
│   │   ├── Deployment: pearl      (OpenAB Helm)
│   │   ├── Deployment: larry      (OpenAB Helm)
│   │   ├── Deployment: conch      (OpenAB Helm)
│   │   ├── Deployment: gary       (自訂 manifest)
│   │   ├── Deployment: gateway    (OpenAB Helm 內建)
│   │   └── Deployment: wecom-bot  (OpenAB Helm)
│   │
│   ├── PersistentVolume: nfs-nas (NFS → NAS)
│   ├── ConfigMap: shared-steering
│   └── Secret: agent-tokens (每 agent 獨立)
│
└── NFS mount: 192.168.1.218:/volume1/KD共用/...
```

---

## 技術決策

| 項目 | 決策 | 原因 |
|---|---|---|
| K8s 發行版 | K3s | 單機部署、輕量、5 分鐘安裝 |
| 部署工具 | Helm | OpenAB 官方提供 chart，直接用 |
| NAS 協定 | NFS（取代 CIFS）| Linux kernel 完整支援 `soft,reconnect` |
| 作業系統 | Ubuntu 24.04 LTS | 穩定、長期支援、社群大 |
| gary-service | 獨立 Deployment | 非 OpenAB agent，需自訂 manifest |
| magic-conch | 移除 | 功能已整合進 gary-service（小蝸）|

---

## 硬體需求

| 項目 | 最低 | 建議 |
|---|---|---|
| CPU | 4 核 | 8 核（每 agent ~0.5 核） |
| RAM | 16 GB | 32 GB（每 agent ~1-2 GB） |
| 磁碟 | 50 GB SSD | 100 GB SSD |
| 網路 | Gigabit，可連 NAS | 同上 |

---

## 遷移步驟（依序執行）

### Phase 1：環境準備
1. 安裝 Ubuntu 24.04 LTS
2. 安裝 K3s：`curl -sfL https://get.k3s.io | sh -`
3. 安裝 Helm：`curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash`
4. 加入 OpenAB Helm repo：`helm repo add openab https://openabdev.github.io/openab`
5. 設定 NFS：請 MIS 在 NAS 開啟 NFS 服務，授權新主機 IP
6. 建立 NFS PersistentVolume + StorageClass

### Phase 2：部署 Agent（逐一遷移）
1. 建立 `bikini-bottom` namespace
2. 建立 Kubernetes Secrets（每 agent 的 token）
3. 準備 `values-bikini-bottom.yaml`（所有 agent 的配置）
4. `helm install bikini-bottom openab/openab -f values-bikini-bottom.yaml`
5. 逐一驗證每個 agent 的 Discord 連線
6. 認證：`kubectl exec -it deployment/bikini-bottom-bob -- kiro-cli login --use-device-flow`

### Phase 3：gary-service（小蝸）遷移
1. 將 `services/slash-bot/` 改名為 `services/gary-service/`
2. 修改 Dockerfile：移除 docker SDK，改用 `kubernetes` Python client
3. 修改 bot.py：`container.restart()` → `kubectl rollout restart deployment/xxx`
4. 撰寫 K8s Deployment manifest（含 ServiceAccount + RBAC 權限）
5. 部署並測試 `/heal`、`/status`、`/logs` 指令

### Phase 4：NAS NFS 掛載
1. 建立 NFS PersistentVolume 指向 NAS
2. 各 agent 透過 `extraVolumeMounts` 掛載 `/nas`
3. Steering 改用 ConfigMap 或 NFS subPath
4. 驗證 NAS 斷線恢復行為（拔網路線測試）

### Phase 5：清理
1. 停止 Windows 上的 Docker Compose 環境
2. 移除 `services/magic-conch/`（功能已整合進 gary-service）
3. 更新 README 和 docs
4. 歸檔 `docker-compose.yml`（保留但標記為 deprecated）

---

## values-bikini-bottom.yaml 範例（草稿）

```yaml
# 所有 agent 共用設定透過 Helm values 管理
# 實際部署時用：helm install bikini-bottom openab/openab -f values-bikini-bottom.yaml

agents:
  bob:
    command: kiro-cli
    args: ["acp", "--trust-all-tools"]
    discord:
      enabled: true
      allowedChannels: ["CHANNEL_ID"]
      allowBotMessages: "mentions"
    env:
      AGENT_NAME: "bob"
      AGENT_SKILLS: "xlsx,pdf,pptx,docx,doc-coauthoring"
      GIT_AUTHOR_NAME: "海綿寶寶 (SpongeBob)"
      GIT_COMMITTER_NAME: "海綿寶寶 (SpongeBob)"
    secretEnv:
      - name: KIRO_API_KEY
        secretName: bob-secrets
        secretKey: kiro-api-key
      - name: GH_TOKEN
        secretName: bob-secrets
        secretKey: gh-token
    persistence:
      enabled: true
      size: 2Gi
    extraVolumeMounts:
      - name: nas
        mountPath: /nas
      - name: steering
        mountPath: /opt/steering
        readOnly: true
    extraVolumes:
      - name: nas
        persistentVolumeClaim:
          claimName: nfs-nas
      - name: steering
        configMap:
          name: shared-steering
    # 其他 agent 同理，只改 name / token / channel
```

---

## gary-service K8s manifest 草稿

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gary
  namespace: bikini-bottom
spec:
  replicas: 1
  selector:
    matchLabels:
      app: gary
  template:
    metadata:
      labels:
        app: gary
    spec:
      serviceAccountName: gary-sa  # 需要 RBAC 權限操作其他 Deployment
      containers:
        - name: gary
          image: ghcr.io/kedingtw/gary-service:latest
          env:
            - name: DISCORD_BOT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: gary-secrets
                  key: discord-bot-token
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gary-sa
  namespace: bikini-bottom
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gary-role
  namespace: bikini-bottom
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "patch"]  # patch = rollout restart
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gary-rolebinding
  namespace: bikini-bottom
subjects:
  - kind: ServiceAccount
    name: gary-sa
roleRef:
  kind: Role
  name: gary-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 風險與注意事項

1. **Kiro CLI 認證** — 每個 agent 首次需手動 `kiro-cli login`，token 存在 PVC 裡
2. **自訂 Dockerfile** — 目前有額外安裝 git、gh、python 套件，可能需要自建 image 或用 `extraInitContainers`
3. **Steering 同步** — 目前用 symlink，K8s 需改用 ConfigMap 或 NFS subPath
4. **Cronjob** — OpenAB chart 支援 `cronjobs` 設定，直接對應目前 `cronjob.toml`
5. **WeCom Gateway** — chart 內建支援，設定 `gateway.enabled=true` + wecom 參數即可
6. **NFS 權限** — 需確認 NAS NFS export 的 uid/gid 與 Pod 的 `runAsUser: 1000` 相容

---

## 參考資料

- OpenAB Helm Chart：`refs/openab/charts/openab/`
- OpenAB K8s Manifests：`refs/openab/k8s/`
- K3s 官方文件：https://docs.k3s.io/
- Helm 官方文件：https://helm.sh/docs/
