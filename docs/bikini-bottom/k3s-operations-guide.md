# 🏝️ 比奇堡 K3s 維運指南

> 寫給有 Docker Compose 經驗但沒碰過 K8s/K3s 的團隊。
> 由淺入深，搭配比奇堡風格插畫幫助理解。

---

## 📖 目錄

1. [為什麼從 Docker Compose 搬到 K3s](#1-為什麼從-docker-compose-搬到-k3s)
2. [概念對照：你已經會的 vs 新學的](#2-概念對照你已經會的-vs-新學的)
3. [架構總覽](#3-架構總覽)
4. [日常維運操作](#4-日常維運操作)
5. [部署與更新流程](#5-部署與更新流程)
6. [監控與觀察](#6-監控與觀察)
7. [常見問題排除](#7-常見問題排除)
8. [NAS 掛載維護](#8-nas-掛載維護)
9. [備份與災難恢復](#9-備份與災難恢復)
10. [資源管理](#10-資源管理)
11. [安全注意事項](#11-安全注意事項)
12. [附錄：命令速查表](#附錄命令速查表)

---

## 1. 為什麼從 Docker Compose 搬到 K3s

![概念圖：Docker Compose vs K3s](images/k3s-vs-compose-final.png)

### Docker Compose 的限制（我們遇到的）

| 痛點 | 具體情境 |
|------|----------|
| NAS 斷線全軍覆沒 | CIFS volume 一斷，所有容器的 `/nas` 變成空的，要手動 `down -v` + `up` |
| 沒有自動恢復 | 容器 OOM 被殺後 `restart: unless-stopped` 會重啟，但不會重新掛載 volume |
| 更新有停機 | `docker compose down && up` 之間有 10~30 秒空窗 |
| 資源互搶 | 一個 agent 狂吃 RAM 時，其他 agent 被拖慢 |

### K3s 怎麼解決

| 解法 | 說明 |
|------|------|
| **自癒（Self-healing）** | Pod 掛了自動重啟，volume 斷了自動重新掛載嘗試 |
| **滾動更新（Rolling Update）** | 更新 image 時，先起新 Pod 再殺舊 Pod，零停機 |
| **資源限制（Resource Limits）** | 每個 Pod 設定 RAM/CPU 上限，不會互相影響 |
| **宣告式管理** | 寫好 YAML「我要什麼狀態」，K3s 自動幫你達成 |

### 什麼是 K3s？

K3s 是 **輕量版 Kubernetes**，由 Rancher 開發。完整 K8s 需要 6 個以上元件分開跑，K3s 把它們打包成一個 binary（~70MB），非常適合：
- 單節點或小規模部署
- 邊緣計算 / IoT
- 開發團隊的內部工具（就是我們）

---

## 2. 概念對照：你已經會的 vs 新學的

> 💡 核心觀念：**K3s 的每個東西，你在 docker compose 裡都用過類似的**。

| 你熟悉的（Docker Compose） | 對應的（K3s） | 一句話解釋 |
|---|---|---|
| `docker-compose.yml` | Deployment YAML | 「我要跑什麼」的定義檔 |
| `services.bob` | `Deployment: bob` | 一個角色 = 一個 Deployment |
| 一個跑起來的 container | 一個 Pod | Pod ≈ container（通常 1:1） |
| `.env` 檔案 | `Secret` | 存放 token、密碼等機密 |
| `environment:` 區塊 | `ConfigMap` + `Secret` | 環境變數來源 |
| `volumes:` | `PersistentVolume` (PV) | 持久化儲存 |
| `build: .` | 預先 build 好的 image | K3s 不 build，只拉 image |
| `restart: unless-stopped` | K3s 內建（永遠重啟） | 更強：會重新排程到健康的地方 |
| `docker compose up -d` | `kubectl apply -f` | 部署 |
| `docker compose down` | `kubectl delete -f` | 刪除 |
| `docker compose logs` | `kubectl logs` | 看 log |
| `docker exec -it` | `kubectl exec -it` | 進容器 |

### 新概念（Docker Compose 沒有的）

![Pod 生命週期](images/k3s-pod-lifecycle-final.png)

| 概念 | 說明 | 為什麼需要 |
|------|------|-----------|
| **Namespace** | 隔離空間，像資料夾 | 把比奇堡所有東西放在 `bikini-bottom` namespace，不跟其他服務混在一起 |
| **ConfigMap** | 非機密的設定值 | Channel ID 這種不算機密但每個 Pod 都要的值 |
| **Liveness Probe** | 健康檢查 | K3s 定期檢查 Pod 有沒有卡死，卡死就自動重啟 |
| **Resource Limits** | CPU/RAM 上限 | 防止某個 Pod 吃光全部記憶體 |
| **Kustomize** | YAML 的「模板引擎」 | 避免重複寫類似的 YAML |

---

## 3. 架構總覽

![架構圖：比奇堡 K3s Cluster](images/k3s-architecture-v4.png)

### 元件配置

```
Ubuntu Desktop 24.04 (16GB RAM)
├── K3s (single-node cluster)
│   └── namespace: bikini-bottom
│       ├── Deployments (每個 agent 一個)
│       │   ├── bob        ← 前端工程師
│       │   ├── patrick    ← 後端工程師
│       │   ├── puff       ← Code Review
│       │   ├── squidward  ← PM
│       │   ├── sandy      ← CSM
│       │   ├── pearl      ← 開發者
│       │   ├── larry      ← 開發者
│       │   ├── conch      ← 神奇海螺
│       │   └── gateway    ← WeCom Gateway
│       │
│       ├── Secrets
│       │   ├── discord-tokens     (各角色 bot token)
│       │   ├── kiro-api-keys      (各角色 API key)
│       │   ├── github-token       (共用 GH_TOKEN)
│       │   └── nas-credentials    (NAS 帳密)
│       │
│       ├── ConfigMaps
│       │   ├── channel-ids        (Discord 頻道 ID)
│       │   └── common-env         (GIT_EMAIL 等共用設定)
│       │
│       └── PersistentVolumes
│           ├── nas-shared         (/mnt/nas → NAS CIFS)
│           └── agent-home-*       (各角色 home 目錄)
│
└── /mnt/nas (systemd automount → NAS Samba)
```

### 網路架構

```
                    Internet
                       │
                  Discord API
                       │
         ┌─────────────┼──────────────┐
         │             │              │
    [bob Pod]    [patrick Pod]   [puff Pod] ...
         │             │              │
         └──────┬──────┘              │
                │                     │
         host.docker.internal:80      │
                │                     │
         [MCP Server]                 │
                                      │
         /mnt/nas ←──── NAS (CIFS) ───┘
```

每個 Pod 用 `hostNetwork: true` 或 K3s 的 host DNS 直接連到 MCP Server，不需要 `extra_hosts`。

---

## 4. 日常維運操作

![日常操作控制台](images/k3s-daily-ops-final.png)

### 4.1 查看所有 Pod 狀態

```bash
# 等同 docker ps
kubectl get pods -n bikini-bottom

# 輸出範例：
# NAME                        READY   STATUS    RESTARTS   AGE
# bob-7d4f8b6c9-x2k4j        1/1     Running   0          3h
# patrick-5c9d7a8b2-m8n3p    1/1     Running   0          3h
# puff-6b3e9c7d1-k5j2l      1/1     Running   0          3h
# squidward-8a2f6d4c3-p9q7r  1/1     Running   0          3h
# ...
```

**STATUS 解讀：**
| 狀態 | 意思 | 要不要管 |
|------|------|---------|
| `Running` | 正常運作中 | ✅ 不用管 |
| `Pending` | 等待排程（可能資源不足） | ⚠️ 檢查資源 |
| `CrashLoopBackOff` | 一直重啟一直失敗 | ❌ 要查 log |
| `ImagePullBackOff` | 拉 image 失敗 | ❌ 檢查 image 是否存在 |
| `Terminating` | 正在關閉 | ⏳ 等一下就好 |

### 4.2 看某個 Agent 的 Log

```bash
# 等同 docker compose logs -f bob
kubectl logs -f deployment/bob -n bikini-bottom

# 看最後 50 行
kubectl logs --tail=50 deployment/bob -n bikini-bottom

# 看之前 crash 掉的 Pod log（很有用！）
kubectl logs deployment/bob -n bikini-bottom --previous
```

### 4.3 進入 Pod 內部（除錯用）

```bash
# 等同 docker exec -it bob bash
kubectl exec -it deployment/bob -n bikini-bottom -- bash

# 進去後就跟以前一樣，可以：
# - 看檔案: ls /home/agent/.kiro/
# - 測 MCP 連線: curl http://host.docker.internal:80/mcp/crm
# - 看環境變數: env | grep DISCORD
```

### 4.4 重啟某個 Agent

```bash
# 等同 docker compose restart bob
kubectl rollout restart deployment/bob -n bikini-bottom

# 差別：K3s 會先起一個新 Pod，確認 Ready 後才殺舊的（零停機）
```

### 4.5 暫停某個 Agent（不刪除設定）

```bash
# 把副本數設為 0（Pod 消失但 Deployment 還在）
kubectl scale deployment/bob -n bikini-bottom --replicas=0

# 恢復
kubectl scale deployment/bob -n bikini-bottom --replicas=1
```

### 4.6 查看 Pod 詳細資訊

```bash
# 當 Pod 狀態異常時，看詳細事件
kubectl describe pod -l app=bob -n bikini-bottom

# 會顯示：
# - Events（最近發生什麼事）
# - Conditions（健康狀態）
# - 為什麼 Pending / 為什麼重啟
```

---

## 5. 部署與更新流程

### 5.1 首次部署（全部）

```bash
# 一鍵部署所有資源
kubectl apply -k k3s/

# 驗證
kubectl get all -n bikini-bottom
```

### 5.2 更新 Image（改了 Dockerfile 後）

```bash
# Step 1: 重新 build image
docker build -t bikini-bottom/agent:latest .

# Step 2: 匯入 K3s
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -

# Step 3: 滾動更新所有 agent
kubectl rollout restart deployment -n bikini-bottom -l type=agent

# 或只更新特定角色
kubectl rollout restart deployment/bob -n bikini-bottom
```

### 5.3 更新設定（改了 config.toml / steering）

```bash
# 情境 A: 改了 agent 的 config.toml
# → config.toml 是 volume mount 的 hostPath，直接改檔案後重啟 Pod
kubectl rollout restart deployment/bob -n bikini-bottom

# 情境 B: 改了 Secret（token / API key）
kubectl create secret generic discord-tokens -n bikini-bottom \
  --from-literal=BOB=新的token \
  --from-literal=PATRICK=新的token \
  --dry-run=client -o yaml | kubectl apply -f -
# 然後重啟受影響的 Pod
kubectl rollout restart deployment/bob -n bikini-bottom

# 情境 C: 改了 ConfigMap（Channel ID 等）
kubectl edit configmap channel-ids -n bikini-bottom
# 儲存後重啟相關 Pod
```

### 5.4 新增一個角色

```bash
# Step 1: 建立角色目錄（跟以前一樣）
mkdir -p agents/新角色/.kiro/settings agents/新角色/.kiro/steering

# Step 2: 寫 config.toml、steering 等

# Step 3: 複製一份現有的 deployment YAML 修改
cp k3s/deployments/bob.yaml k3s/deployments/新角色.yaml
# 改 name、token 引用、volume path

# Step 4: 加入 kustomization.yaml

# Step 5: 部署
kubectl apply -k k3s/
```

### 5.5 查看更新進度

```bash
# 看滾動更新狀態
kubectl rollout status deployment/bob -n bikini-bottom

# 輸出：
# Waiting for deployment "bob" rollout to finish: 1 old replicas are pending termination...
# deployment "bob" successfully rolled out
```

---

## 6. 監控與觀察

### 6.1 資源用量

```bash
# 等同 docker stats
kubectl top pods -n bikini-bottom

# 輸出：
# NAME                        CPU(cores)   MEMORY(bytes)
# bob-7d4f8b6c9-x2k4j        15m          180Mi
# patrick-5c9d7a8b2-m8n3p    8m           150Mi
# ...

# 看 Node 整體用量
kubectl top node
```

### 6.2 事件（Event）

```bash
# 看最近的事件（K3s 自動記錄所有重要操作）
kubectl get events -n bikini-bottom --sort-by='.lastTimestamp'

# 常見事件：
# - Pod 被 OOM Kill
# - Image pull 失敗
# - Volume mount 失敗
# - Liveness probe 失敗 → 重啟
```

### 6.3 持續監控（watch 模式）

```bash
# 持續刷新 Pod 狀態（Ctrl+C 停止）
kubectl get pods -n bikini-bottom -w

# 持續看某個 Pod 的 log
kubectl logs -f deployment/bob -n bikini-bottom
```

---

## 7. 常見問題排除

![問題排除指南](images/k3s-troubleshooting-final.png)

### 7.1 Pod 一直 CrashLoopBackOff

**症狀**：Pod 不斷重啟，STATUS 顯示 `CrashLoopBackOff`

```bash
# Step 1: 看 log 找死因
kubectl logs deployment/bob -n bikini-bottom --previous

# Step 2: 看事件
kubectl describe pod -l app=bob -n bikini-bottom | tail -20

# 常見原因：
# - Token 無效 → 更新 Secret
# - Kiro API Key 過期 → 更新 Secret
# - config.toml 語法錯 → 修正後 restart
# - Image 版本不對 → 重新 build + import
```

**修復**：
```bash
# 假設是 token 問題
kubectl create secret generic discord-tokens -n bikini-bottom \
  --from-literal=BOB=新token \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/bob -n bikini-bottom
```

### 7.2 NAS 掛載失敗

**症狀**：Pod 卡在 `Pending` 或 agent 讀不到 `/nas` 內容

```bash
# Step 1: 檢查 host 上 NAS 掛載
mount | grep nas
ls /mnt/nas/shared/

# Step 2: 如果沒掛載，手動重掛
sudo mount -a

# Step 3: 如果掛載正常但 Pod 裡看不到
# → 重啟 Pod（讓它重新 bind mount）
kubectl rollout restart deployment/bob -n bikini-bottom
```

**預防**：systemd automount 會在存取時自動掛載，但如果 NAS 完全離線就要等 NAS 恢復。

### 7.3 OOM Killed（記憶體不足被殺）

**症狀**：Pod 突然重啟，`describe` 裡看到 `OOMKilled`

```bash
kubectl describe pod -l app=bob -n bikini-bottom | grep -A5 "Last State"
# → Reason: OOMKilled
```

**修復**：
```bash
# 方式 A: 提高該 Pod 的 memory limit
# 編輯 deployment YAML，把 limits.memory 從 512Mi 改成 768Mi

# 方式 B: 減少同時運行的 Pod 數量
kubectl scale deployment/pearl -n bikini-bottom --replicas=0
```

### 7.4 Image 更新後 Pod 還是跑舊版

**原因**：K3s 用了快取的舊 image

```bash
# 強制重新載入
docker build -t bikini-bottom/agent:v2 .  # 改版號
docker save bikini-bottom/agent:v2 | sudo k3s ctr images import -

# 更新 deployment 指定新版號
kubectl set image deployment/bob agent=bikini-bottom/agent:v2 -n bikini-bottom
```

### 7.5 kubectl 連不上

```bash
# 檢查 K3s 服務
sudo systemctl status k3s

# 如果停了
sudo systemctl start k3s

# 檢查 kubeconfig
echo $KUBECONFIG
cat ~/.kube/config | head -5
```

---

## 8. NAS 掛載維護

### 掛載方式

K3s 環境下 NAS 掛載分兩層：

1. **Host 層**：Ubuntu 用 systemd automount 把 NAS 掛到 `/mnt/nas`
2. **Pod 層**：Deployment YAML 用 `hostPath` 把 `/mnt/nas` 掛進 Pod

### 日常檢查

```bash
# 確認 NAS 掛載正常
df -h | grep nas
# //192.168.1.218/...  4.0T  2.1T  1.9T  53% /mnt/nas

# 確認 Pod 裡能讀到
kubectl exec deployment/bob -n bikini-bottom -- ls /nas/shared/
```

### NAS 斷線恢復

```bash
# 如果 NAS 斷線後恢復了，通常 systemd automount 會自動重連
# 但如果卡住：
sudo umount -l /mnt/nas
sudo mount -a

# 然後重啟所有 agent Pod
kubectl rollout restart deployment -n bikini-bottom -l type=agent
```

### fstab 設定（參考）

```
//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom /mnt/nas cifs credentials=/etc/nas-credentials,file_mode=0777,dir_mode=0777,vers=3.0,iocharset=utf8,echo_interval=10,_netdev,x-systemd.automount 0 0
```

重點參數：
- `_netdev`：等網路好了再掛
- `x-systemd.automount`：第一次存取時才真正掛載，斷線後自動重試
- `echo_interval=10`：每 10 秒偵測連線

---

## 9. 備份與災難恢復

### 備份什麼

| 項目 | 位置 | 備份方式 |
|------|------|----------|
| K3s 設定 | `/etc/rancher/k3s/` | 定期 cp |
| 部署 YAML | `k3s/` 目錄（Git 版控） | git push |
| Agent home | `/home/agent/`（或 NAS） | NAS 自帶備份 |
| Secrets | K3s etcd 內 | `kubectl get secret -o yaml` 導出 |

### 導出所有 Secret（定期備份）

```bash
kubectl get secrets -n bikini-bottom -o yaml > backup/secrets-$(date +%Y%m%d).yaml
# ⚠️ 這個檔案包含所有 token，要安全存放！
```

### 災難恢復（整台機器掛了）

```bash
# 1. 重裝 Ubuntu + K3s
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik" sh -

# 2. 掛載 NAS
sudo mount -a

# 3. Build image
docker build -t bikini-bottom/agent:latest .
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -

# 4. 還原 Secrets
kubectl apply -f backup/secrets-最新日期.yaml

# 5. 部署全部
kubectl apply -k k3s/

# 完成！所有 agent 恢復運作
```

---

## 10. 資源管理

### 目前配置（16 GB RAM）

```yaml
# 每個 agent Pod 的資源限制
resources:
  requests:          # 保證最少給這麼多
    memory: "128Mi"
    cpu: "50m"       # 0.05 核
  limits:            # 最多只能用這麼多
    memory: "512Mi"
    cpu: "500m"      # 0.5 核
```

### 資源分配建議

| 角色類型 | memory limit | 說明 |
|---------|-------------|------|
| Agent (bob, patrick...) | 512Mi | 含 kiro-cli session |
| gateway | 128Mi | 純轉發 |
| conch | 512Mi | 同 agent |

### 當記憶體升級到 32 GB

```yaml
# 可以放寬限制
resources:
  requests:
    memory: "256Mi"
  limits:
    memory: "1Gi"    # 讓 agent 處理大任務時有空間
```

### 監控資源趨勢

```bash
# 看當前用量
kubectl top pods -n bikini-bottom

# 如果安裝了 metrics-server（K3s 內建）
# 可以看歷史趨勢
kubectl top pods -n bikini-bottom --sort-by=memory
```

---

## 11. 安全注意事項

### Secret 管理

```bash
# ❌ 不要這樣（明文寫在 YAML 裡 commit 到 git）
# apiVersion: v1
# data:
#   token: 明文token

# ✅ 用 kubectl 建立 Secret（不進 git）
kubectl create secret generic discord-tokens -n bikini-bottom \
  --from-literal=BOB=實際token \
  --from-literal=PATRICK=實際token

# ✅ 或用 .env 檔案匯入（.env 在 .gitignore 裡）
kubectl create secret generic discord-tokens -n bikini-bottom \
  --from-env-file=.env.discord-tokens
```

### 網路安全

- K3s 單節點下所有 Pod 共用 host 網路，彼此能互連
- MCP Server 在同網段，Pod 用 `host.docker.internal` 或直接用內網 IP 連
- 不需要暴露任何 port 到公網（除了 gateway 的 8080，如果用 WeCom）

### RBAC（未來多人管理時）

目前單人管理不需要，但之後如果多人共用 cluster：
```bash
# 可以建立只能操作 bikini-bottom namespace 的 ServiceAccount
# 限制誰能 delete、誰只能 get/logs
```

---

## 附錄：命令速查表

### 最常用（每天會用到）

```bash
# 看所有 Pod 狀態
kubectl get pods -n bikini-bottom

# 看某個 agent log
kubectl logs -f deploy/bob -n bikini-bottom

# 重啟某個 agent
kubectl rollout restart deploy/bob -n bikini-bottom

# 看資源用量
kubectl top pods -n bikini-bottom
```

### 部署相關

```bash
# 部署全部
kubectl apply -k k3s/

# 更新 image 後重新部署
docker build -t bikini-bottom/agent:latest .
docker save bikini-bottom/agent:latest | sudo k3s ctr images import -
kubectl rollout restart deploy -n bikini-bottom -l type=agent

# 暫停某個角色
kubectl scale deploy/pearl -n bikini-bottom --replicas=0

# 恢復
kubectl scale deploy/pearl -n bikini-bottom --replicas=1
```

### 除錯相關

```bash
# 進 Pod
kubectl exec -it deploy/bob -n bikini-bottom -- bash

# 看 Pod 詳細（為什麼 Pending / 為什麼重啟）
kubectl describe pod -l app=bob -n bikini-bottom

# 看上一次 crash 的 log
kubectl logs deploy/bob -n bikini-bottom --previous

# 看 namespace 裡所有事件
kubectl get events -n bikini-bottom --sort-by='.lastTimestamp'
```

### Secret / ConfigMap

```bash
# 看有哪些 Secret
kubectl get secrets -n bikini-bottom

# 更新 Secret
kubectl create secret generic discord-tokens -n bikini-bottom \
  --from-literal=BOB=新token --dry-run=client -o yaml | kubectl apply -f -

# 看 ConfigMap 內容
kubectl get configmap channel-ids -n bikini-bottom -o yaml
```

### 整個 Cluster

```bash
# 看 Node 狀態
kubectl get nodes

# 看 K3s 服務狀態
sudo systemctl status k3s

# 重啟 K3s（極端情況才需要）
sudo systemctl restart k3s
```

---

## 🏝️ 小結

從 Docker Compose 到 K3s，日常操作的心智模型不變：

1. **看狀態** → `get pods`（原 `docker ps`）
2. **看 log** → `kubectl logs`（原 `docker logs`）
3. **重啟** → `rollout restart`（原 `docker restart`）
4. **進容器** → `kubectl exec`（原 `docker exec`）
5. **部署** → `kubectl apply`（原 `docker compose up`）

最大的改變是從「手動管理」變成「宣告式管理」——你寫好「我要 bob 跑著、用這個 image、掛這些 volume」，K3s 會確保它一直是這個狀態。Pod 死了？自動拉起來。NAS 斷了重連？自動重掛。你不用再半夜爬起來手動 restart。

有問題隨時問，比奇堡不會沉沒的 🍍
