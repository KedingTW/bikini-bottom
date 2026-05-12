#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# 🏝️ SSM Parameter Store 初始化腳本
# 將所有 secrets 寫入 SSM Parameter Store（免費）
#
# 用法: 填入下方變數後執行
#   ./infra/setup-ssm-params.sh
# ─────────────────────────────────────────────────────────────

REGION="us-east-1"

# ═══ 請填入實際值 ═══════════════════════════════════════════
DISCORD_BOT_TOKEN_BOB=""
DISCORD_BOT_TOKEN_PATRICK=""
DISCORD_BOT_TOKEN_PUFF=""
DISCORD_BOT_TOKEN_GARY=""

CHANNEL_GENERAL=""
KIRO_USAGE_CHANNEL_ID=""
DISCORD_GUILD_ID=""
SLASH_BOT_CHANNEL_ID=""

GH_TOKEN=""
GIT_EMAIL=""

# Bob 專用 AWS credentials（用於 Athena 等）
AWS_ACCESS_KEY_ID_BOB=""
AWS_SECRET_ACCESS_KEY_BOB=""

# Config URLs（每個角色的 GitHub Gist raw URL）
CONFIG_URL_BOB=""
CONFIG_URL_PATRICK=""
CONFIG_URL_PUFF=""
# ═══════════════════════════════════════════════════════════════

put() {
  local name=$1 value=$2 type=${3:-SecureString}
  if [ -z "$value" ]; then
    echo "[SKIP] $name (empty value)"
    return
  fi
  aws ssm put-parameter \
    --name "$name" \
    --value "$value" \
    --type "$type" \
    --overwrite \
    --region $REGION >/dev/null
  echo "[OK]   $name"
}

echo "Writing SSM parameters to ${REGION}..."
echo ""

# ─── Per-agent secrets ─────────────────────────────────
put "/bikini-bottom/bob/discord-bot-token"     "$DISCORD_BOT_TOKEN_BOB"
put "/bikini-bottom/patrick/discord-bot-token"  "$DISCORD_BOT_TOKEN_PATRICK"
put "/bikini-bottom/puff/discord-bot-token"     "$DISCORD_BOT_TOKEN_PUFF"
put "/bikini-bottom/gary/discord-bot-token"     "$DISCORD_BOT_TOKEN_GARY"

# ─── Gary (slash-bot) specific ─────────────────────────
put "/bikini-bottom/gary/guild-id"              "$DISCORD_GUILD_ID"
put "/bikini-bottom/gary/slash-bot-channel-id"  "$SLASH_BOT_CHANNEL_ID"

# ─── Shared secrets ───────────────────────────────────
put "/bikini-bottom/shared/channel-general"     "$CHANNEL_GENERAL"
put "/bikini-bottom/shared/kiro-usage-channel"  "$KIRO_USAGE_CHANNEL_ID"
put "/bikini-bottom/shared/gh-token"            "$GH_TOKEN"
put "/bikini-bottom/shared/git-email"           "$GIT_EMAIL"
put "/bikini-bottom/shared/aws-access-key-id"   "$AWS_ACCESS_KEY_ID_BOB"
put "/bikini-bottom/shared/aws-secret-access-key" "$AWS_SECRET_ACCESS_KEY_BOB"

# ─── Config URLs (String, not SecureString) ────────────
put "/bikini-bottom/bob/config-url"     "$CONFIG_URL_BOB"     "String"
put "/bikini-bottom/patrick/config-url" "$CONFIG_URL_PATRICK" "String"
put "/bikini-bottom/puff/config-url"    "$CONFIG_URL_PUFF"    "String"

echo ""
echo "✅ Done! All parameters stored in /bikini-bottom/*"
echo ""
echo "Next steps:"
echo "  1. Create GitHub Gists for each agent's config.toml"
echo "  2. Fill in CONFIG_URL_* and re-run this script"
echo "  3. Run ./infra/deploy.sh"
