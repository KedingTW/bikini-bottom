#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ 比奇堡 ECS Fargate Spot 資源清除腳本
# 用法:
#   ./infra/destroy.sh          # 清除全部
#   ./infra/destroy.sh services # 只刪 ECS services（保留 VPC/ECR）
#   ./infra/destroy.sh all      # 清除全部（含 VPC）
#
# 可反覆執行，已刪除的資源會跳過。
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"
CLUSTER_NAME="bikini-bottom"
ECR_REPO_NAME="bikini-bottom/openab"
ECR_REPO_SLASH="bikini-bottom/slash-bot"
S3_BUCKET_PREFIX="bikini-bottom-state"
LOG_GROUP="/ecs/bikini-bottom"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

SERVICES=("bb-bob" "bb-patrick" "bb-puff" "bb-gary")

log() { echo "$(date '+%H:%M:%S') [INFO] $*"; }
warn() { echo "$(date '+%H:%M:%S') [WARN] $*"; }

# ─── 刪除 ECS Services ────────────────────────────────
destroy_services() {
  log "Deleting ECS services..."

  for svc in "${SERVICES[@]}"; do
    STATUS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $svc \
      --region $REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")

    if [ "$STATUS" = "ACTIVE" ]; then
      # 先設 desired count 為 0
      aws ecs update-service --cluster $CLUSTER_NAME --service $svc \
        --desired-count 0 --region $REGION >/dev/null 2>&1 || true
      # 刪除 service
      aws ecs delete-service --cluster $CLUSTER_NAME --service $svc \
        --force --region $REGION >/dev/null 2>&1 || true
      log "  Deleted service: $svc"
    else
      warn "  Service $svc not found or already deleted"
    fi
  done

  # 等待 tasks 停止
  log "Waiting for tasks to stop..."
  sleep 10
}

# ─── 刪除 Task Definitions ────────────────────────────
destroy_task_definitions() {
  log "Deregistering task definitions..."

  for family in bb-bob bb-patrick bb-puff bb-gary; do
    # 列出所有 active revisions
    REVISIONS=$(aws ecs list-task-definitions --family-prefix $family \
      --status ACTIVE --region $REGION \
      --query 'taskDefinitionArns[]' --output text 2>/dev/null || echo "")

    for rev in $REVISIONS; do
      aws ecs deregister-task-definition --task-definition $rev --region $REGION >/dev/null 2>&1 || true
      log "  Deregistered: $rev"
    done
  done
}

# ─── 刪除 ECS Cluster ─────────────────────────────────
destroy_cluster() {
  log "Deleting ECS cluster..."

  CLUSTER_STATUS=$(aws ecs describe-clusters --clusters $CLUSTER_NAME \
    --region $REGION --query 'clusters[0].status' --output text 2>/dev/null || echo "MISSING")

  if [ "$CLUSTER_STATUS" = "ACTIVE" ]; then
    aws ecs delete-cluster --cluster $CLUSTER_NAME --region $REGION >/dev/null 2>&1 || true
    log "  Deleted cluster: $CLUSTER_NAME"
  else
    warn "  Cluster not found or already deleted"
  fi
}

# ─── 刪除 S3 Bucket ───────────────────────────────────
destroy_s3() {
  S3_BUCKET="${S3_BUCKET_PREFIX}-${ACCOUNT_ID}"
  log "Deleting S3 bucket: $S3_BUCKET"

  if aws s3api head-bucket --bucket $S3_BUCKET --region $REGION 2>/dev/null; then
    aws s3 rm s3://$S3_BUCKET --recursive --region $REGION 2>/dev/null || true
    aws s3 rb s3://$S3_BUCKET --region $REGION 2>/dev/null || true
    log "  Deleted bucket: $S3_BUCKET"
  else
    warn "  Bucket not found"
  fi
}

# ─── 刪除 CloudWatch Log Group ────────────────────────
destroy_logs() {
  log "Deleting log group: $LOG_GROUP"
  aws logs delete-log-group --log-group-name $LOG_GROUP --region $REGION 2>/dev/null || \
    warn "  Log group not found"
}

# ─── 刪除 ECR Repositories ────────────────────────────
destroy_ecr() {
  log "Deleting ECR repositories..."

  for repo in $ECR_REPO_NAME $ECR_REPO_SLASH; do
    if aws ecr describe-repositories --repository-names $repo --region $REGION >/dev/null 2>&1; then
      aws ecr delete-repository --repository-name $repo --force --region $REGION >/dev/null 2>&1
      log "  Deleted ECR: $repo"
    else
      warn "  ECR repo $repo not found"
    fi
  done
}

# ─── 刪除 IAM Roles ───────────────────────────────────
destroy_iam() {
  log "Deleting IAM roles..."

  for role in bikini-bottom-exec bikini-bottom-task; do
    if aws iam get-role --role-name $role >/dev/null 2>&1; then
      # 移除 inline policies
      POLICIES=$(aws iam list-role-policies --role-name $role --query 'PolicyNames[]' --output text 2>/dev/null || echo "")
      for pol in $POLICIES; do
        aws iam delete-role-policy --role-name $role --policy-name $pol 2>/dev/null || true
      done

      # 移除 attached policies
      ATTACHED=$(aws iam list-attached-role-policies --role-name $role --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
      for arn in $ATTACHED; do
        aws iam detach-role-policy --role-name $role --policy-arn $arn 2>/dev/null || true
      done

      aws iam delete-role --role-name $role 2>/dev/null || true
      log "  Deleted role: $role"
    else
      warn "  Role $role not found"
    fi
  done
}

# ─── 刪除 SSM Parameters ──────────────────────────────
destroy_ssm() {
  log "Deleting SSM parameters under /bikini-bottom/..."

  PARAMS=$(aws ssm get-parameters-by-path --path "/bikini-bottom" --recursive \
    --region $REGION --query 'Parameters[].Name' --output text 2>/dev/null || echo "")

  if [ -n "$PARAMS" ]; then
    for param in $PARAMS; do
      aws ssm delete-parameter --name "$param" --region $REGION 2>/dev/null || true
      log "  Deleted: $param"
    done
  else
    warn "  No SSM parameters found"
  fi
}

# ─── 刪除 VPC ─────────────────────────────────────────
destroy_vpc() {
  log "Deleting VPC..."

  VPC_ID=$(aws ec2 describe-vpcs --region $REGION \
    --filters "Name=tag:Name,Values=bikini-bottom-vpc" \
    --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "None")

  if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    warn "  VPC not found"
    return
  fi

  # 刪除 subnets
  SUBNETS=$(aws ec2 describe-subnets --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[].SubnetId' --output text 2>/dev/null || echo "")
  for sub in $SUBNETS; do
    aws ec2 delete-subnet --subnet-id $sub --region $REGION 2>/dev/null || true
    log "  Deleted subnet: $sub"
  done

  # 刪除 route table（非 main）
  RTS=$(aws ec2 describe-route-tables --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=bikini-bottom-public-rt" \
    --query 'RouteTables[].RouteTableId' --output text 2>/dev/null || echo "")
  for rt in $RTS; do
    # 先解除 association
    ASSOCS=$(aws ec2 describe-route-tables --route-table-ids $rt --region $REGION \
      --query 'RouteTables[0].Associations[?!Main].RouteTableAssociationId' --output text 2>/dev/null || echo "")
    for assoc in $ASSOCS; do
      aws ec2 disassociate-route-table --association-id $assoc --region $REGION 2>/dev/null || true
    done
    aws ec2 delete-route-table --route-table-id $rt --region $REGION 2>/dev/null || true
    log "  Deleted route table: $rt"
  done

  # 刪除 internet gateway
  IGWS=$(aws ec2 describe-internet-gateways --region $REGION \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query 'InternetGateways[].InternetGatewayId' --output text 2>/dev/null || echo "")
  for igw in $IGWS; do
    aws ec2 detach-internet-gateway --internet-gateway-id $igw --vpc-id $VPC_ID --region $REGION 2>/dev/null || true
    aws ec2 delete-internet-gateway --internet-gateway-id $igw --region $REGION 2>/dev/null || true
    log "  Deleted IGW: $igw"
  done

  # 刪除 security groups（非 default）
  SGS=$(aws ec2 describe-security-groups --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text 2>/dev/null || echo "")
  for sg in $SGS; do
    aws ec2 delete-security-group --group-id $sg --region $REGION 2>/dev/null || true
    log "  Deleted SG: $sg"
  done

  # 刪除 VPC
  aws ec2 delete-vpc --vpc-id $VPC_ID --region $REGION 2>/dev/null || true
  log "  Deleted VPC: $VPC_ID"
}

# ─── Main ──────────────────────────────────────────────
TARGET=${1:-all}

echo ""
echo "⚠️  This will DELETE all bikini-bottom resources in ${REGION}!"
echo "    Target: ${TARGET}"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted."
  exit 0
fi
echo ""

case $TARGET in
  services)
    destroy_services
    ;;
  all)
    destroy_services
    destroy_task_definitions
    destroy_cluster
    destroy_s3
    destroy_logs
    destroy_ecr
    destroy_iam
    destroy_ssm
    destroy_vpc
    # 清除 local env file
    rm -f infra/.env.infra
    ;;
  *)
    echo "Usage: $0 [services|all]"
    echo "  services — only delete ECS services (keep infra)"
    echo "  all      — delete everything"
    exit 1
    ;;
esac

echo ""
log "🧹 Cleanup complete!"
