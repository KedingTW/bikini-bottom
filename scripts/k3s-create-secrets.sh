#!/bin/bash
# 🏝️ 從 .env 建立 K8s Secrets
# 用法: bash scripts/k3s-create-secrets.sh

set -e

ENV_FILE=".env"
NAMESPACE="bikini-bottom"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 找不到 .env 檔案。請從舊機複製過來。"
  exit 1
fi

# 載入 .env
set -a
source "$ENV_FILE"
set +a

echo "🔐 從 .env 建立 K8s Secrets..."
echo "   Namespace: $NAMESPACE"
echo ""

# 確保 namespace 存在
kubectl get namespace $NAMESPACE &>/dev/null || kubectl create namespace $NAMESPACE

# ─── Discord Bot Tokens ───
echo "  📌 discord-tokens..."
kubectl create secret generic discord-tokens -n $NAMESPACE \
  --from-literal=BOB="${DISCORD_BOT_TOKEN_BOB}" \
  --from-literal=PATRICK="${DISCORD_BOT_TOKEN_PATRICK}" \
  --from-literal=PUFF="${DISCORD_BOT_TOKEN_PUFF}" \
  --from-literal=SQUIDWARD="${DISCORD_BOT_TOKEN_SQUIDWARD}" \
  --from-literal=SANDY="${DISCORD_BOT_TOKEN_SANDY}" \
  --from-literal=CONCH="${DISCORD_BOT_TOKEN_CONCH}" \
  --from-literal=PEARL="${DISCORD_BOT_TOKEN_PEARL}" \
  --from-literal=LARRY="${DISCORD_BOT_TOKEN_LARRY}" \
  --from-literal=GARY="${DISCORD_BOT_TOKEN_GARY}" \
  --dry-run=client -o yaml | kubectl apply -f -

# ─── Kiro API Keys ───
echo "  📌 kiro-api-keys..."
kubectl create secret generic kiro-api-keys -n $NAMESPACE \
  --from-literal=BOB="${KIRO_API_KEY_BOB}" \
  --from-literal=PATRICK="${KIRO_API_KEY_PATRICK}" \
  --from-literal=PUFF="${KIRO_API_KEY_PUFF}" \
  --from-literal=SQUIDWARD="${KIRO_API_KEY_SQUIDWARD}" \
  --from-literal=SANDY="${KIRO_API_KEY_SANDY}" \
  --from-literal=CONCH="${KIRO_API_KEY_CONCH}" \
  --from-literal=PEARL="${KIRO_API_KEY_PEARL}" \
  --from-literal=LARRY="${KIRO_API_KEY_LARRY}" \
  --dry-run=client -o yaml | kubectl apply -f -

# ─── GitHub Token ───
echo "  📌 github-token..."
kubectl create secret generic github-token -n $NAMESPACE \
  --from-literal=GH_TOKEN="${GH_TOKEN}" \
  --dry-run=client -o yaml | kubectl apply -f -

# ─── Slash Bot ───
echo "  📌 slash-bot-secrets..."
kubectl create secret generic slash-bot-secrets -n $NAMESPACE \
  --from-literal=DISCORD_BOT_TOKEN="${DISCORD_BOT_TOKEN_GARY}" \
  --from-literal=AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
  --from-literal=AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
  --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✅ 所有 Secrets 建立完成！"
echo ""
echo "驗證: kubectl get secrets -n $NAMESPACE"
