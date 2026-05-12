# Fargate 規格調整 SOP

當 agent 出現 OOM（Out of Memory）或效能不足時，依此 SOP 調整。

## 症狀判斷

| 症狀 | 原因 | 解法 |
|------|------|------|
| Task 頻繁重啟、exit code 137 | OOM killed | 增加 memory |
| Agent 回應極慢、CPU throttled | CPU 不足 | 增加 CPU |
| 多 session 時部分 session 無回應 | 記憶體不足 | 增加 memory |

## 可用規格

| CPU | Memory 選項 | Spot 月費估算 |
|-----|-------------|--------------|
| 256 (0.25 vCPU) | 512 MB, 1 GB, 2 GB | $2.7 / $3.4 / $4.7 |
| 512 (0.5 vCPU) | 1 GB, 2 GB, 3 GB, 4 GB | $5.4 / $6.7 / $8.0 / $9.4 |
| 1024 (1 vCPU) | 2 GB ~ 8 GB | $10.7 ~ $18.8 |

## 調整步驟

### 1. 確認需要調整的角色

```bash
# 查看最近的 stopped tasks 和原因
aws ecs list-tasks --cluster bikini-bottom --service-name bb-<AGENT> \
  --desired-status STOPPED --region us-east-1

# 查看 task 停止原因
aws ecs describe-tasks --cluster bikini-bottom --tasks <TASK_ARN> \
  --region us-east-1 --query 'tasks[0].{reason:stoppedReason,exit:containers[0].exitCode}'
```

### 2. 更新 Task Definition

編輯 `infra/deploy.sh` 中對應角色的 task definition，修改 `cpu` 和 `memory`：

```bash
# 例：將 bob 升級到 0.5 vCPU / 1 GB
# 修改 /tmp/td-bob.json 中的：
#   "cpu": "512",
#   "memory": "1024",
```

或直接用 AWS CLI：

```bash
# 取得當前 task definition
aws ecs describe-task-definition --task-definition bb-bob --region us-east-1 \
  --query 'taskDefinition' > /tmp/td-bob-current.json

# 修改 cpu/memory 後重新註冊
# （需移除 taskDefinitionArn, revision, status, registeredAt, registeredBy, requiresAttributes, compatibilities）
aws ecs register-task-definition --cli-input-json file:///tmp/td-bob-updated.json --region us-east-1

# 更新 service 使用新版本
aws ecs update-service --cluster bikini-bottom --service bb-bob \
  --task-definition bb-bob --force-new-deployment --region us-east-1
```

### 3. 快速指令（一行搞定）

```bash
# 升級 bob 到 512 CPU / 1024 Memory
./infra/scale-agent.sh bob 512 1024
```

### 4. 驗證

```bash
# 確認新 task 啟動成功
aws ecs describe-services --cluster bikini-bottom --services bb-bob \
  --region us-east-1 --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'

# 看 log
aws logs tail /ecs/bikini-bottom --log-stream-name-prefix bob --follow --region us-east-1
```

## 建議

- 先從 0.25 vCPU / 512 MB 開始
- 如果 `max_sessions` > 3，建議至少 1 GB memory
- 如果 `max_sessions` > 5，建議 0.5 vCPU / 2 GB
- Puff（Code Review）通常不需要多 session，512 MB 足夠
