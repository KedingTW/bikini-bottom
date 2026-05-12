#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ Agent 規格調整腳本
# 用法:
#   ./infra/scale-agent.sh bob 512 1024    # 升到 0.5 vCPU / 1 GB
#   ./infra/scale-agent.sh puff 256 512    # 降回 0.25 vCPU / 512 MB
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"
CLUSTER="bikini-bottom"

AGENT=${1:?Usage: $0 <agent> <cpu> <memory>}
NEW_CPU=${2:?Usage: $0 <agent> <cpu> <memory>}
NEW_MEM=${3:?Usage: $0 <agent> <cpu> <memory>}

FAMILY="bb-${AGENT}"

echo "📐 Scaling ${AGENT}: CPU=${NEW_CPU}, Memory=${NEW_MEM}"

# 取得當前 task definition（去掉不可重新註冊的欄位）
CURRENT=$(aws ecs describe-task-definition --task-definition $FAMILY --region $REGION \
  --query 'taskDefinition' --output json)

# 用 python 修改 cpu/memory 並清理欄位
NEW_TD=$(echo "$CURRENT" | python3 -c "
import json, sys
td = json.load(sys.stdin)
td['cpu'] = '${NEW_CPU}'
td['memory'] = '${NEW_MEM}'
for key in ['taskDefinitionArn','revision','status','registeredAt','registeredBy','requiresAttributes','compatibilities']:
    td.pop(key, None)
print(json.dumps(td))
")

echo "$NEW_TD" > /tmp/td-${AGENT}-scaled.json

aws ecs register-task-definition --cli-input-json file:///tmp/td-${AGENT}-scaled.json --region $REGION >/dev/null
echo "✅ Registered new task definition"

aws ecs update-service --cluster $CLUSTER --service $FAMILY \
  --task-definition $FAMILY --force-new-deployment --region $REGION >/dev/null
echo "✅ Service updated, new task deploying..."

echo ""
echo "Monitor: aws ecs describe-services --cluster $CLUSTER --services $FAMILY --region $REGION --query 'services[0].{running:runningCount,pending:pendingCount}'"
