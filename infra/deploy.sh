#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ 比奇堡 ECS Fargate Spot 一鍵部署腳本
# 用法:
#   ./infra/deploy.sh          # 部署全部
#   ./infra/deploy.sh bob      # 只部署 bob
#   ./infra/deploy.sh vpc      # 只建 VPC
#   ./infra/deploy.sh ecr      # 只建 ECR + push image
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"
CLUSTER_NAME="bikini-bottom"
ECR_REPO_NAME="bikini-bottom/openab"
ECR_REPO_SLASH="bikini-bottom/slash-bot"
S3_BUCKET_PREFIX="bikini-bottom-state"
LOG_GROUP="/ecs/bikini-bottom"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# 角色清單
AGENTS=("bob" "patrick" "puff")

# ─── 工具函式 ──────────────────────────────────────────
log() { echo "$(date '+%H:%M:%S') [INFO] $*"; }
err() { echo "$(date '+%H:%M:%S') [ERROR] $*" >&2; exit 1; }

check_prereqs() {
  command -v aws >/dev/null || err "aws CLI not found"
  command -v docker >/dev/null || err "docker not found"
  aws sts get-caller-identity >/dev/null 2>&1 || err "AWS credentials not configured"
  log "AWS Account: ${ACCOUNT_ID}, Region: ${REGION}"
}

# ─── Phase 1: VPC ──────────────────────────────────────
deploy_vpc() {
  log "Creating VPC..."

  # 檢查是否已存在
  EXISTING_VPC=$(aws ec2 describe-vpcs --region $REGION \
    --filters "Name=tag:Name,Values=bikini-bottom-vpc" \
    --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "None")

  if [ "$EXISTING_VPC" != "None" ] && [ "$EXISTING_VPC" != "" ]; then
    log "VPC already exists: $EXISTING_VPC"
    VPC_ID=$EXISTING_VPC
  else
    VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
      --region $REGION \
      --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=bikini-bottom-vpc}]' \
      --query 'Vpc.VpcId' --output text)
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $REGION
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $REGION
    log "Created VPC: $VPC_ID"
  fi

  # Internet Gateway
  IGW_ID=$(aws ec2 describe-internet-gateways --region $REGION \
    --filters "Name=attachment.vpc-id,Values=$VPC_ID" \
    --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null || echo "None")

  if [ "$IGW_ID" = "None" ] || [ "$IGW_ID" = "" ]; then
    IGW_ID=$(aws ec2 create-internet-gateway --region $REGION \
      --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=bikini-bottom-igw}]' \
      --query 'InternetGateway.InternetGatewayId' --output text)
    aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
    log "Created IGW: $IGW_ID"
  else
    log "IGW already exists: $IGW_ID"
  fi

  # Public Subnets (2 AZs for ECS)
  SUBNET_A=$(aws ec2 describe-subnets --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=bikini-bottom-public-a" \
    --query 'Subnets[0].SubnetId' --output text 2>/dev/null || echo "None")

  if [ "$SUBNET_A" = "None" ] || [ "$SUBNET_A" = "" ]; then
    SUBNET_A=$(aws ec2 create-subnet --vpc-id $VPC_ID \
      --cidr-block 10.0.1.0/24 --availability-zone ${REGION}a \
      --region $REGION \
      --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=bikini-bottom-public-a}]' \
      --query 'Subnet.SubnetId' --output text)
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET_A --map-public-ip-on-launch --region $REGION
    log "Created Subnet A: $SUBNET_A"
  fi

  SUBNET_B=$(aws ec2 describe-subnets --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=bikini-bottom-public-b" \
    --query 'Subnets[0].SubnetId' --output text 2>/dev/null || echo "None")

  if [ "$SUBNET_B" = "None" ] || [ "$SUBNET_B" = "" ]; then
    SUBNET_B=$(aws ec2 create-subnet --vpc-id $VPC_ID \
      --cidr-block 10.0.2.0/24 --availability-zone ${REGION}b \
      --region $REGION \
      --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=bikini-bottom-public-b}]' \
      --query 'Subnet.SubnetId' --output text)
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET_B --map-public-ip-on-launch --region $REGION
    log "Created Subnet B: $SUBNET_B"
  fi

  # Route Table
  RT_ID=$(aws ec2 describe-route-tables --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=bikini-bottom-public-rt" \
    --query 'RouteTables[0].RouteTableId' --output text 2>/dev/null || echo "None")

  if [ "$RT_ID" = "None" ] || [ "$RT_ID" = "" ]; then
    RT_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --region $REGION \
      --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=bikini-bottom-public-rt}]' \
      --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 \
      --gateway-id $IGW_ID --region $REGION
    aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_A --region $REGION
    aws ec2 associate-route-table --route-table-id $RT_ID --subnet-id $SUBNET_B --region $REGION
    log "Created Route Table: $RT_ID"
  fi

  # Security Group
  SG_ID=$(aws ec2 describe-security-groups --region $REGION \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=bikini-bottom-sg" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")

  if [ "$SG_ID" = "None" ] || [ "$SG_ID" = "" ]; then
    SG_ID=$(aws ec2 create-security-group \
      --group-name bikini-bottom-sg \
      --description "Bikini Bottom ECS - egress only" \
      --vpc-id $VPC_ID --region $REGION \
      --query 'GroupId' --output text)
    # 預設已有 all-outbound，不需額外設定
    log "Created Security Group: $SG_ID"
  fi

  # 輸出
  log "VPC setup complete!"
  log "  VPC_ID=$VPC_ID"
  log "  SUBNET_A=$SUBNET_A"
  log "  SUBNET_B=$SUBNET_B"
  log "  SG_ID=$SG_ID"

  # 寫入 env file 供後續步驟使用
  cat > infra/.env.infra << EOF
VPC_ID=$VPC_ID
SUBNET_A=$SUBNET_A
SUBNET_B=$SUBNET_B
SG_ID=$SG_ID
IGW_ID=$IGW_ID
EOF
}

# ─── Phase 2: ECR + Build + Upload Configs ────────────
deploy_ecr() {
  log "Setting up ECR..."

  # OpenAB image
  aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $REGION

  # Slash-bot image
  aws ecr describe-repositories --repository-names $ECR_REPO_SLASH --region $REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPO_SLASH --region $REGION

  # Login to ECR
  aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ECR_URI

  # Build & push OpenAB image
  log "Building OpenAB image..."
  docker build -t ${ECR_URI}/${ECR_REPO_NAME}:latest .
  docker push ${ECR_URI}/${ECR_REPO_NAME}:latest

  # Build & push slash-bot image
  log "Building slash-bot image..."
  docker build -t ${ECR_URI}/${ECR_REPO_SLASH}:latest ./services/slash-bot/
  docker push ${ECR_URI}/${ECR_REPO_SLASH}:latest

  # Upload config files to S3
  S3_BUCKET="${S3_BUCKET_PREFIX}-${ACCOUNT_ID}"
  log "Uploading config files to S3..."
  for agent in "${AGENTS[@]}"; do
    if [ -f "infra/configs/${agent}.toml" ]; then
      aws s3 cp "infra/configs/${agent}.toml" "s3://${S3_BUCKET}/configs/${agent}.toml" --region $REGION
      log "  Uploaded config: ${agent}.toml"
    fi
  done

  log "ECR + configs done!"
}

# ─── Phase 3: IAM Roles ───────────────────────────────
deploy_iam() {
  log "Creating IAM roles..."

  TRUST_POLICY='{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"ecs-tasks.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

  S3_BUCKET="${S3_BUCKET_PREFIX}-${ACCOUNT_ID}"

  # Execution Role
  aws iam get-role --role-name bikini-bottom-exec >/dev/null 2>&1 || \
    aws iam create-role --role-name bikini-bottom-exec \
      --assume-role-policy-document "$TRUST_POLICY"

  aws iam attach-role-policy --role-name bikini-bottom-exec \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || true

  aws iam put-role-policy --role-name bikini-bottom-exec \
    --policy-name ssm-read \
    --policy-document '{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Action":["ssm:GetParameters","ssm:GetParameter"],
        "Resource":"arn:aws:ssm:*:'$ACCOUNT_ID':parameter/bikini-bottom/*"
      }]
    }'

  # Task Role
  aws iam get-role --role-name bikini-bottom-task >/dev/null 2>&1 || \
    aws iam create-role --role-name bikini-bottom-task \
      --assume-role-policy-document "$TRUST_POLICY"

  aws iam put-role-policy --role-name bikini-bottom-task \
    --policy-name s3-and-exec \
    --policy-document '{
      "Version":"2012-10-17",
      "Statement":[
        {
          "Effect":"Allow",
          "Action":["s3:GetObject","s3:PutObject","s3:ListBucket","s3:DeleteObject"],
          "Resource":["arn:aws:s3:::'$S3_BUCKET'","arn:aws:s3:::'$S3_BUCKET'/*"]
        },
        {
          "Effect":"Allow",
          "Action":["ssmmessages:CreateControlChannel","ssmmessages:CreateDataChannel","ssmmessages:OpenControlChannel","ssmmessages:OpenDataChannel"],
          "Resource":"*"
        }
      ]
    }'

  log "IAM roles ready"
}

# ─── Phase 4: S3 + Logs + Cluster ─────────────────────
deploy_infra() {
  log "Creating S3, Logs, Cluster..."

  S3_BUCKET="${S3_BUCKET_PREFIX}-${ACCOUNT_ID}"

  # S3
  aws s3api head-bucket --bucket $S3_BUCKET --region $REGION 2>/dev/null || \
    aws s3 mb s3://$S3_BUCKET --region $REGION

  # CloudWatch Logs
  aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --region $REGION \
    --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q "$LOG_GROUP" || \
    aws logs create-log-group --log-group-name $LOG_GROUP --region $REGION

  aws logs put-retention-policy --log-group-name $LOG_GROUP --retention-in-days 3 --region $REGION

  # ECS Cluster
  aws ecs describe-clusters --clusters $CLUSTER_NAME --region $REGION \
    --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE" || \
    aws ecs create-cluster --cluster-name $CLUSTER_NAME \
      --capacity-providers FARGATE_SPOT FARGATE \
      --default-capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1,base=1 \
      --region $REGION

  log "Infrastructure ready"
}

# ─── Phase 5: Deploy Agent ─────────────────────────────
deploy_agent() {
  local AGENT_NAME=$1
  log "Deploying agent: $AGENT_NAME"

  source infra/.env.infra 2>/dev/null || err "Run 'deploy.sh vpc' first"

  S3_BUCKET="${S3_BUCKET_PREFIX}-${ACCOUNT_ID}"
  IMAGE="${ECR_URI}/${ECR_REPO_NAME}:latest"
  CONFIG_S3="s3://${S3_BUCKET}/configs/${AGENT_NAME}.toml"

  # 確認 config 存在
  aws s3 ls "$CONFIG_S3" --region $REGION >/dev/null 2>&1 || \
    err "Config not found: ${CONFIG_S3}. Run 'deploy.sh ecr' first to upload configs."

  # 額外 secrets（bob 有 AWS credentials 和 KIRO_USAGE_CHANNEL_ID）
  EXTRA_SECRETS=""
  if [ "$AGENT_NAME" = "bob" ]; then
    EXTRA_SECRETS=',
        {"name": "KIRO_USAGE_CHANNEL_ID", "valueFrom": "arn:aws:ssm:'${REGION}':'${ACCOUNT_ID}':parameter/bikini-bottom/shared/kiro-usage-channel"},
        {"name": "AWS_ACCESS_KEY_ID", "valueFrom": "arn:aws:ssm:'${REGION}':'${ACCOUNT_ID}':parameter/bikini-bottom/shared/aws-access-key-id"},
        {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:ssm:'${REGION}':'${ACCOUNT_ID}':parameter/bikini-bottom/shared/aws-secret-access-key"}'
  fi

  # Git identity per agent
  case $AGENT_NAME in
    bob)     GIT_NAME="海綿寶寶 (SpongeBob)" ;;
    patrick) GIT_NAME="派大星 (Patrick)" ;;
    puff)    GIT_NAME="泡芙老師 (Mrs. Puff)" ;;
    *)       GIT_NAME="$AGENT_NAME" ;;
  esac

  # 產生 task definition
  cat > /tmp/td-${AGENT_NAME}.json << TASKDEF
{
  "family": "bb-${AGENT_NAME}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/bikini-bottom-exec",
  "taskRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/bikini-bottom-task",
  "containerDefinitions": [
    {
      "name": "s3-restore",
      "image": "amazon/aws-cli",
      "essential": false,
      "command": ["sh", "-c", "aws s3 cp s3://${S3_BUCKET}/${AGENT_NAME}/auth/ /data/auth/ --recursive 2>/dev/null || true; aws s3 cp s3://${S3_BUCKET}/configs/${AGENT_NAME}.toml /data/config.toml 2>/dev/null || true; [ -f /data/auth/data.sqlite3 ] && chown 1000:1000 /data/auth/data.sqlite3; exit 0"],
      "mountPoints": [{"sourceVolume": "agent-data", "containerPath": "/data"}],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {"awslogs-group": "${LOG_GROUP}", "awslogs-region": "${REGION}", "awslogs-stream-prefix": "${AGENT_NAME}-init"}
      }
    },
    {
      "name": "openab",
      "image": "${IMAGE}",
      "essential": true,
      "dependsOn": [{"containerName": "s3-restore", "condition": "SUCCESS"}],
      "entryPoint": ["sh", "-c"],
      "command": ["[ -f /data/auth/data.sqlite3 ] && cp /data/auth/data.sqlite3 /home/agent/.local/share/kiro-cli/data.sqlite3; exec tini -- openab run -c /data/config.toml"],
      "environment": [
        {"name": "HOME", "value": "/home/agent"},
        {"name": "GIT_AUTHOR_NAME", "value": "${GIT_NAME}"},
        {"name": "GIT_COMMITTER_NAME", "value": "${GIT_NAME}"}
      ],
      "secrets": [
        {"name": "DISCORD_BOT_TOKEN", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/${AGENT_NAME}/discord-bot-token"},
        {"name": "GH_TOKEN", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/gh-token"},
        {"name": "CHANNEL_GENERAL", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/channel-general"},
        {"name": "GIT_AUTHOR_EMAIL", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/git-email"},
        {"name": "GIT_COMMITTER_EMAIL", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/git-email"}${EXTRA_SECRETS}
      ],
      "mountPoints": [{"sourceVolume": "agent-data", "containerPath": "/data"}],
      "user": "1000:1000",
      "healthCheck": {
        "command": ["CMD-SHELL", "pgrep -x openab || exit 1"],
        "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 20
      },
      "stopTimeout": 30,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {"awslogs-group": "${LOG_GROUP}", "awslogs-region": "${REGION}", "awslogs-stream-prefix": "${AGENT_NAME}"}
      }
    },
    {
      "name": "s3-sync",
      "image": "amazon/aws-cli",
      "essential": false,
      "dependsOn": [{"containerName": "openab", "condition": "START"}],
      "command": ["sh", "-c", "while true; do sleep 300; cp /proc/1/root/home/agent/.local/share/kiro-cli/data.sqlite3 /data/auth/data.sqlite3 2>/dev/null && aws s3 cp /data/auth/data.sqlite3 s3://${S3_BUCKET}/${AGENT_NAME}/auth/data.sqlite3 2>/dev/null; done"],
      "mountPoints": [{"sourceVolume": "agent-data", "containerPath": "/data"}],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {"awslogs-group": "${LOG_GROUP}", "awslogs-region": "${REGION}", "awslogs-stream-prefix": "${AGENT_NAME}-sync"}
      }
    }
  ],
  "volumes": [{"name": "agent-data"}]
}
TASKDEF

  aws ecs register-task-definition --cli-input-json file:///tmp/td-${AGENT_NAME}.json --region $REGION
  log "Registered task definition: bb-${AGENT_NAME}"

  # Create or update service
  SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services bb-${AGENT_NAME} \
    --region $REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")

  if [ "$SERVICE_EXISTS" = "ACTIVE" ]; then
    aws ecs update-service --cluster $CLUSTER_NAME --service bb-${AGENT_NAME} \
      --task-definition bb-${AGENT_NAME} --force-new-deployment --region $REGION >/dev/null
    log "Updated service: bb-${AGENT_NAME}"
  else
    aws ecs create-service \
      --cluster $CLUSTER_NAME \
      --service-name bb-${AGENT_NAME} \
      --task-definition bb-${AGENT_NAME} \
      --desired-count 1 \
      --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1,base=1 \
      --network-configuration "{\"awsvpcConfiguration\":{\"subnets\":[\"${SUBNET_A}\",\"${SUBNET_B}\"],\"securityGroups\":[\"${SG_ID}\"],\"assignPublicIp\":\"ENABLED\"}}" \
      --deployment-configuration '{"maximumPercent":200,"minimumHealthyPercent":0}' \
      --enable-execute-command \
      --region $REGION >/dev/null
    log "Created service: bb-${AGENT_NAME}"
  fi
}

# ─── Phase 6: Deploy slash-bot (gary) ─────────────────
deploy_gary() {
  log "Deploying gary (slash-bot)..."

  source infra/.env.infra 2>/dev/null || err "Run 'deploy.sh vpc' first"

  IMAGE="${ECR_URI}/${ECR_REPO_SLASH}:latest"

  cat > /tmp/td-gary.json << TASKDEF
{
  "family": "bb-gary",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/bikini-bottom-exec",
  "taskRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/bikini-bottom-task",
  "containerDefinitions": [
    {
      "name": "slash-bot",
      "image": "${IMAGE}",
      "essential": true,
      "secrets": [
        {"name": "DISCORD_BOT_TOKEN", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/gary/discord-bot-token"},
        {"name": "DISCORD_GUILD_ID", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/gary/guild-id"},
        {"name": "SLASH_BOT_CHANNEL_ID", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/gary/slash-bot-channel-id"},
        {"name": "AWS_ACCESS_KEY_ID", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/aws-access-key-id"},
        {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/bikini-bottom/shared/aws-secret-access-key"}
      ],
      "environment": [
        {"name": "AWS_DEFAULT_REGION", "value": "us-east-1"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "python -c 'import os; exit(0)' || exit 1"],
        "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 10
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {"awslogs-group": "${LOG_GROUP}", "awslogs-region": "${REGION}", "awslogs-stream-prefix": "gary"}
      }
    }
  ]
}
TASKDEF

  aws ecs register-task-definition --cli-input-json file:///tmp/td-gary.json --region $REGION

  SERVICE_EXISTS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services bb-gary \
    --region $REGION --query 'services[0].status' --output text 2>/dev/null || echo "MISSING")

  if [ "$SERVICE_EXISTS" = "ACTIVE" ]; then
    aws ecs update-service --cluster $CLUSTER_NAME --service bb-gary \
      --task-definition bb-gary --force-new-deployment --region $REGION >/dev/null
    log "Updated service: bb-gary"
  else
    aws ecs create-service \
      --cluster $CLUSTER_NAME \
      --service-name bb-gary \
      --task-definition bb-gary \
      --desired-count 1 \
      --capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=1,base=1 \
      --network-configuration "{\"awsvpcConfiguration\":{\"subnets\":[\"${SUBNET_A}\",\"${SUBNET_B}\"],\"securityGroups\":[\"${SG_ID}\"],\"assignPublicIp\":\"ENABLED\"}}" \
      --deployment-configuration '{"maximumPercent":200,"minimumHealthyPercent":0}' \
      --enable-execute-command \
      --region $REGION >/dev/null
    log "Created service: bb-gary"
  fi
}

# ─── Main ──────────────────────────────────────────────
check_prereqs

TARGET=${1:-all}

case $TARGET in
  vpc)    deploy_vpc ;;
  ecr)    deploy_ecr ;;
  iam)    deploy_iam ;;
  infra)  deploy_infra ;;
  bob|patrick|puff)
    deploy_agent $TARGET ;;
  gary)
    deploy_gary ;;
  all)
    deploy_vpc
    deploy_iam
    deploy_infra
    deploy_ecr
    for agent in "${AGENTS[@]}"; do
      deploy_agent $agent
    done
    deploy_gary
    log ""
    log "🎉 All services deployed!"
    log ""
    log "Next: run first-time auth for each OAB agent:"
    log "  ./infra/login-agent.sh bob"
    log "  ./infra/login-agent.sh patrick"
    log "  ./infra/login-agent.sh puff"
    ;;
  *)
    echo "Usage: $0 [vpc|ecr|iam|infra|bob|patrick|puff|gary|all]"
    exit 1
    ;;
esac
