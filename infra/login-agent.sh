#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ Agent 首次認證腳本
# 用法:
#   ./infra/login-agent.sh bob
#   ./infra/login-agent.sh patrick
#   ./infra/login-agent.sh puff
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"
CLUSTER="bikini-bottom"
AGENT=${1:?Usage: $0 <agent-name>}
SERVICE="bb-${AGENT}"

echo "🔑 Logging in agent: ${AGENT}"
echo ""

# 找到 running task
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE \
  --desired-status RUNNING --region $REGION \
  --query 'taskArns[0]' --output text)

if [ "$TASK_ARN" = "None" ] || [ -z "$TASK_ARN" ]; then
  echo "❌ No running task found for service ${SERVICE}"
  echo "   Check: aws ecs describe-services --cluster $CLUSTER --services $SERVICE --region $REGION"
  exit 1
fi

TASK_ID=$(echo $TASK_ARN | awk -F/ '{print $NF}')
echo "📦 Task: ${TASK_ID}"
echo ""
echo "Step 1: Running kiro-cli login..."
echo "        Follow the device flow URL in your browser."
echo ""

aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK_ID \
  --container openab \
  --interactive \
  --region $REGION \
  --command "kiro-cli login --use-device-flow"

echo ""
echo "Step 2: Copying auth to shared volume for S3 backup..."

aws ecs execute-command \
  --cluster $CLUSTER \
  --task $TASK_ID \
  --container openab \
  --interactive \
  --region $REGION \
  --command "cp /home/agent/.local/share/kiro-cli/data.sqlite3 /data/data.sqlite3"

echo ""
echo "✅ Done! Auth will be synced to S3 within 5 minutes."
echo "   Future task restarts will auto-restore from S3."
