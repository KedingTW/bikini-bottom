#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ SSM Parameter Store 初始化腳本
# 直接從 .env 讀取，不需要手動填入
#
# 用法:
#   ./infra/setup-ssm-params.sh
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ .env file not found at: $ENV_FILE"
  exit 1
fi

# Source .env（跳過註解和空行）
set -a
source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
set +a

echo "📝 Writing SSM parameters to ${REGION}..."
echo "   Source: ${ENV_FILE}"
echo ""

put() {
  local name=$1 value=$2 type=${3:-SecureString}
  if [ -z "${value:-}" ]; then
    echo "[SKIP] $name (empty)"
    return
  fi
  aws ssm put-parameter \
    --name "$name" \
    --value "$value" \
    --type "$type" \
    --overwrite \
    --region $REGION >/dev/null 2>&1
  echo "[OK]   $name"
}

# ─── Per-agent Discord tokens ─────────────────────────
put "/bikini-bottom/bob/discord-bot-token"      "${DISCORD_BOT_TOKEN_BOB:-}"
put "/bikini-bottom/patrick/discord-bot-token"   "${DISCORD_BOT_TOKEN_PATRICK:-}"
put "/bikini-bottom/puff/discord-bot-token"      "${DISCORD_BOT_TOKEN_PUFF:-}"
put "/bikini-bottom/gary/discord-bot-token"      "${DISCORD_BOT_TOKEN_GARY:-}"

# ─── Shared ───────────────────────────────────────────
put "/bikini-bottom/shared/channel-general"      "${CHANNEL_GENERAL:-}"
put "/bikini-bottom/shared/kiro-usage-channel"   "${KIRO_USAGE_CHANNEL_ID:-}"
put "/bikini-bottom/shared/gh-token"             "${GH_TOKEN:-}"
put "/bikini-bottom/shared/git-email"            "${GIT_EMAIL:-}"
put "/bikini-bottom/shared/aws-access-key-id"    "${AWS_ACCESS_KEY_ID:-}"
put "/bikini-bottom/shared/aws-secret-access-key" "${AWS_SECRET_ACCESS_KEY:-}"

# ─── Gary (slash-bot) ─────────────────────────────────
put "/bikini-bottom/gary/guild-id"               "${DISCORD_GUILD_ID:-}"
put "/bikini-bottom/gary/slash-bot-channel-id"   "${SLASH_BOT_CHANNEL_ID:-}"

echo ""
echo "✅ Done! All parameters stored in /bikini-bottom/*"
