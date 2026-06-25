#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# secrets-sync.sh — 自動同步 .env.new 的敏感值到 AWS Secrets Manager
#
# 用法：
#   ./scripts/secrets-sync.sh              # 建立或更新所有 secrets
#   ./scripts/secrets-sync.sh --dry-run    # 只顯示要做什麼，不實際執行
#   ./scripts/secrets-sync.sh --diff       # 比較本地 vs AWS SM 的差異
#   ./scripts/secrets-sync.sh --pull       # 從 AWS SM 拉回到 .env.new
#
# 前提：
#   - 已安裝 aws cli + jq
#   - AWS credential 已設定（env / profile / SSO）
#   - .env.new 存在且有值
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
REGION="${AWS_REGION:-ap-northeast-1}"

# ─── 定義哪些 key 屬於哪個 secret ───
# 格式：secret_name|key1,key2,key3,...

declare -A SECRET_MAP

SECRET_MAP["openab/bikini-bottom"]="
BIKINI_BOTTOM_KIRO_API_KEY
BIKINI_BOTTOM_BOB_BOT_TOKEN
BIKINI_BOTTOM_PATRICK_BOT_TOKEN
BIKINI_BOTTOM_PUFF_BOT_TOKEN
BIKINI_BOTTOM_SQUIDWARD_BOT_TOKEN
BIKINI_BOTTOM_SANDY_BOT_TOKEN
BIKINI_BOTTOM_GARY_BOT_TOKEN
BIKINI_BOTTOM_CONCH_BOT_TOKEN
BIKINI_BOTTOM_PEARL_BOT_TOKEN
BIKINI_BOTTOM_LARRY_BOT_TOKEN
BIKINI_BOTTOM_MERMAID_MAN_BOT_TOKEN
BIKINI_BOTTOM_KAREN_BOT_TOKEN
GH_TOKEN
OPENAI_API_KEY
OPENAI_ADMIN_KEY
NAS_PASSWORD
ZEABUR_KEY
DASHBOARD_SESSION_SECRET
DASHBOARD_DEFAULT_PASSWORD
REDMINE_API_KEY_BOB
"

SECRET_MAP["openab/keding-dc"]="
KEDING_DC_ORDER_TRANSFORM_BOT_TOKEN
KEDING_DC_ORDER_TRANSFORM_KIRO_KEY
"

SECRET_MAP["openab/keding-wecom"]="
KEDING_WECOM_ORDER_TRANSFORM_SECRET
KEDING_WECOM_ORDER_TRANSFORM_TOKEN
KEDING_WECOM_ORDER_TRANSFORM_ENCODING_AES_KEY
KEDING_WECOM_ORDER_TRANSFORM_KIRO_KEY
"

# ─── Helper functions ───

read_env_file() {
    # Parse .env.new into an associative array (skips comments and empty lines)
    declare -gA ENV_VALUES
    while IFS= read -r line; do
        # Skip comments and empty lines
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # Extract key=value
        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*) ]]; then
            local key="${BASH_REMATCH[1]}"
            local val="${BASH_REMATCH[2]}"
            ENV_VALUES["$key"]="$val"
        fi
    done < "$ENV_FILE"
}

build_json_for_secret() {
    local secret_name="$1"
    local keys="${SECRET_MAP[$secret_name]}"
    local json="{"
    local first=true

    for key in $keys; do
        local val="${ENV_VALUES[$key]:-}"
        # Skip empty values
        [[ -z "$val" ]] && continue

        if [[ "$first" == "true" ]]; then
            first=false
        else
            json+=","
        fi
        # Escape special JSON characters in value
        val=$(echo -n "$val" | jq -Rs '.')
        json+="\"$key\":$val"
    done
    json+="}"
    echo "$json"
}

secret_exists() {
    local secret_name="$1"
    aws secretsmanager describe-secret \
        --secret-id "$secret_name" \
        --region "$REGION" &>/dev/null 2>&1
}

create_secret() {
    local secret_name="$1"
    local json="$2"
    echo "  🆕 建立 secret: $secret_name"
    aws secretsmanager create-secret \
        --name "$secret_name" \
        --description "OpenAB secrets for $(basename "$secret_name")" \
        --secret-string "$json" \
        --region "$REGION" \
        --output text --query 'ARN'
}

update_secret() {
    local secret_name="$1"
    local json="$2"
    echo "  🔄 更新 secret: $secret_name"
    aws secretsmanager put-secret-value \
        --secret-id "$secret_name" \
        --secret-string "$json" \
        --region "$REGION" \
        --output text --query 'ARN'
}

get_remote_secret() {
    local secret_name="$1"
    aws secretsmanager get-secret-value \
        --secret-id "$secret_name" \
        --region "$REGION" \
        --query SecretString --output text 2>/dev/null || echo "{}"
}

# ─── Commands ───

cmd_sync() {
    local dry_run="${1:-false}"
    echo "━━━ Secrets Sync: .env → AWS Secrets Manager ━━━"
    echo "    Region: $REGION"
    echo "    Source: $ENV_FILE"
    echo ""

    read_env_file

    for secret_name in "${!SECRET_MAP[@]}"; do
        local json
        json=$(build_json_for_secret "$secret_name")
        local key_count
        key_count=$(echo "$json" | jq 'keys | length')

        echo "📦 $secret_name ($key_count keys)"

        if [[ "$dry_run" == "true" ]]; then
            echo "  [dry-run] 會寫入以下 keys:"
            echo "$json" | jq -r 'keys[]' | sed 's/^/    - /'
            echo ""
            continue
        fi

        if secret_exists "$secret_name"; then
            update_secret "$secret_name" "$json"
        else
            create_secret "$secret_name" "$json"
        fi
        echo ""
    done

    if [[ "$dry_run" == "false" ]]; then
        echo "✅ 同步完成！"
    fi
}

cmd_diff() {
    echo "━━━ Secrets Diff: .env vs AWS Secrets Manager ━━━"
    echo ""

    read_env_file

    for secret_name in "${!SECRET_MAP[@]}"; do
        echo "📦 $secret_name"

        local remote_json
        remote_json=$(get_remote_secret "$secret_name")

        if [[ "$remote_json" == "{}" ]]; then
            echo "  ⚠️  遠端不存在（尚未建立）"
            echo ""
            continue
        fi

        local keys="${SECRET_MAP[$secret_name]}"
        local has_diff=false

        for key in $keys; do
            local local_val="${ENV_VALUES[$key]:-}"
            local remote_val
            remote_val=$(echo "$remote_json" | jq -r ".[\"$key\"] // \"\"")

            if [[ -z "$local_val" && -z "$remote_val" ]]; then
                continue
            elif [[ "$local_val" != "$remote_val" ]]; then
                has_diff=true
                if [[ -z "$remote_val" ]]; then
                    echo "  + $key (本地有，遠端無)"
                elif [[ -z "$local_val" ]]; then
                    echo "  - $key (遠端有，本地無)"
                else
                    # 只顯示前後 4 字元，避免洩漏
                    local l_preview="${local_val:0:4}...${local_val: -4}"
                    local r_preview="${remote_val:0:4}...${remote_val: -4}"
                    echo "  ≠ $key (本地: ${l_preview} | 遠端: ${r_preview})"
                fi
            fi
        done

        if [[ "$has_diff" == "false" ]]; then
            echo "  ✅ 一致"
        fi
        echo ""
    done
}

cmd_pull() {
    echo "━━━ Secrets Pull: AWS Secrets Manager → .env ━━━"
    echo "⚠️  這會覆蓋 .env.new 中對應 key 的值！"
    read -rp "確定？(y/N) " confirm
    [[ "$confirm" != "y" && "$confirm" != "Y" ]] && echo "取消。" && exit 0

    read_env_file

    for secret_name in "${!SECRET_MAP[@]}"; do
        local remote_json
        remote_json=$(get_remote_secret "$secret_name")
        [[ "$remote_json" == "{}" ]] && continue

        local keys="${SECRET_MAP[$secret_name]}"
        for key in $keys; do
            local remote_val
            remote_val=$(echo "$remote_json" | jq -r ".[\"$key\"] // \"\"")
            [[ -z "$remote_val" ]] && continue

            # Update in .env.new using sed
            if grep -q "^${key}=" "$ENV_FILE"; then
                sed -i "s|^${key}=.*|${key}=${remote_val}|" "$ENV_FILE"
                echo "  ✅ $key 已更新"
            fi
        done
    done

    echo ""
    echo "✅ Pull 完成！"
}

# ─── Main ───

case "${1:-}" in
    --dry-run)
        cmd_sync true
        ;;
    --diff)
        cmd_diff
        ;;
    --pull)
        cmd_pull
        ;;
    --help|-h)
        echo "用法："
        echo "  $0              同步 .env.new → AWS SM（建立或更新）"
        echo "  $0 --dry-run    只顯示計畫，不執行"
        echo "  $0 --diff       比較本地 vs 遠端差異"
        echo "  $0 --pull       從 AWS SM 拉回值到 .env.new"
        echo "  $0 --help       顯示此說明"
        ;;
    "")
        cmd_sync false
        ;;
    *)
        echo "❌ 未知參數: $1"
        echo "   執行 $0 --help 查看用法"
        exit 1
        ;;
esac
