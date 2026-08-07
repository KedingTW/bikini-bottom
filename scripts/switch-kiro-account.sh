#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Kiro 帳號切換腳本
# 功能：停 agent → 切換 .env API key + IDE token → 重啟 agent
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -euo pipefail

# ─── 設定 ───
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
TOKEN_DIR="$HOME/.aws/sso/cache"
TOKEN_FILE="$TOKEN_DIR/kiro-auth-token.json"

# 帳號名稱（對應 .env 行尾的 # Bikini-Bottom-N 註解）
ACCOUNTS=("Bikini-Bottom-1" "Bikini-Bottom-2" "Bikini-Bottom-3")

# K3s namespace 清單
NAMESPACES=("bikini-bottom" "keding-dc")

# ─── 函式 ───

# 取得目前啟用的帳號編號
get_active_account() {
    local active_line
    active_line=$(grep -n '^KIRO_API_KEY=' "$ENV_FILE" | grep -v '^#' | head -1)
    if [ -z "$active_line" ]; then
        echo "0"
        return
    fi
    local line_content
    line_content=$(echo "$active_line" | cut -d: -f2-)
    for i in "${!ACCOUNTS[@]}"; do
        if echo "$line_content" | grep -q "${ACCOUNTS[$i]}"; then
            echo "$((i + 1))"
            return
        fi
    done
    echo "0"
}

# 停止所有 agent pod（scale to 0）
stop_agents() {
    echo "⏹️  停止所有 agent pod..."
    for ns in "${NAMESPACES[@]}"; do
        echo "  停止 namespace: $ns"
        kubectl scale deployment --all --replicas=0 -n "$ns" 2>/dev/null || true
    done
    echo "✅ 所有 agent 已停止"
}

# 重啟所有 agent pod（scale back to 1）
start_agents() {
    echo "▶️  重啟所有 agent pod..."
    for ns in "${NAMESPACES[@]}"; do
        echo "  啟動 namespace: $ns"
        kubectl scale deployment --all --replicas=1 -n "$ns" 2>/dev/null || true
    done
    echo "✅ 所有 agent 已重啟（使用新 API key）"
}

# 切換 .env 中的 KIRO_API_KEY
switch_env_key() {
    local target=$1
    local target_name="${ACCOUNTS[$((target - 1))]}"

    # 把目前啟用的行加上 # 註解
    sed -i "s/^KIRO_API_KEY=\(.*\)/# KIRO_API_KEY=\1/" "$ENV_FILE"

    # 把目標帳號的行去掉 # 註解
    sed -i "s/^# KIRO_API_KEY=\(.*# ${target_name}\)$/KIRO_API_KEY=\1/" "$ENV_FILE"
}

# 更新 K8s Secret
update_k8s_secret() {
    local new_key
    new_key=$(grep '^KIRO_API_KEY=' "$ENV_FILE" | head -1 | sed 's/KIRO_API_KEY=\([^ ]*\).*/\1/')
    if [ -z "$new_key" ]; then
        echo "❌ 無法從 .env 讀取 KIRO_API_KEY"
        exit 1
    fi
    echo "更新 K8s Secret kiro-api-keys..."
    kubectl create secret generic kiro-api-keys -n bikini-bottom \
        --from-literal=BOB="$new_key" \
        --from-literal=CONCH="$new_key" \
        --from-literal=GARY="$new_key" \
        --from-literal=KAREN="$new_key" \
        --from-literal=LARRY="$new_key" \
        --from-literal=MERMAID_MAN="$new_key" \
        --from-literal=PATRICK="$new_key" \
        --from-literal=PEARL="$new_key" \
        --from-literal=PUFF="$new_key" \
        --from-literal=SANDY="$new_key" \
        --from-literal=SQUIDWARD="$new_key" \
        --from-literal=WECOM_BOT="$new_key" \
        --from-literal=WECOM_BOT_ORDER_TRANSFORM="$new_key" \
        --dry-run=client -o yaml | kubectl apply -f -
    echo "✅ K8s Secret 已更新（key: ${new_key:0:8}...）"
}

# 切換 Kiro IDE token
switch_token() {
    local target=$1
    local current_account=$2
    local target_token="$TOKEN_DIR/kiro-auth-token-${target}.json"

    # 先備份當前帳號的 token
    if [ "$current_account" != "0" ] && [ -f "$TOKEN_FILE" ]; then
        cp "$TOKEN_FILE" "$TOKEN_DIR/kiro-auth-token-${current_account}.json"
        echo "✅ 已備份帳號 ${current_account} 的 token"
    fi

    # 嘗試切換到目標 token
    if [ ! -f "$target_token" ]; then
        echo ""
        echo "⚠️  找不到帳號 ${target} 的 token 備份：$target_token"
        echo "   請手動在 Kiro IDE 用帳號 ${target} 登入，登入後執行："
        echo "   cp $TOKEN_FILE $target_token"
        echo ""
        return 1
    fi

    cp "$target_token" "$TOKEN_FILE"
    echo "✅ IDE token 已切換到帳號 ${target}"
    return 0
}

# ─── 主程式 ───

# 子命令：--start 單純重啟 agent
if [ "${1:-}" == "--start" ]; then
    start_agents
    exit 0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔑 Kiro 帳號切換工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 顯示目前狀態
current=$(get_active_account)
if [ "$current" == "0" ]; then
    echo "⚠️  無法偵測目前啟用的帳號"
else
    echo "目前啟用：${ACCOUNTS[$((current - 1))]} (#${current})"
fi
echo ""

# 列出可用帳號
echo "可用帳號："
for i in "${!ACCOUNTS[@]}"; do
    local_num=$((i + 1))
    marker=""
    if [ "$local_num" == "$current" ]; then
        marker=" ← 目前"
    fi
    token_status="❌ 無 token"
    if [ -f "$TOKEN_DIR/kiro-auth-token-${local_num}.json" ]; then
        token_status="✅ 有 token"
    fi
    if [ "$local_num" == "$current" ] && [ -f "$TOKEN_FILE" ]; then
        token_status="✅ 有 token"
    fi
    echo "  ${local_num}) ${ACCOUNTS[$i]}  [${token_status}]${marker}"
done
echo ""

# 選擇目標
read -rp "切換到哪個帳號？(1-${#ACCOUNTS[@]}) " target

# 驗證輸入
if ! [[ "$target" =~ ^[0-9]+$ ]] || [ "$target" -lt 1 ] || [ "$target" -gt "${#ACCOUNTS[@]}" ]; then
    echo "❌ 無效的選擇"
    exit 1
fi

if [ "$target" == "$current" ]; then
    echo "已經是帳號 ${target}，不需切換。"
    exit 0
fi

echo ""
echo "切換：${ACCOUNTS[$((current - 1))]} → ${ACCOUNTS[$((target - 1))]}"
echo ""

# ─── Step 1: 停止 agent ───
stop_agents
echo ""

# ─── Step 2: 切換 .env ───
switch_env_key "$target"
echo "✅ .env KIRO_API_KEY 已切換到 ${ACCOUNTS[$((target - 1))]}"
echo ""

# ─── Step 3: 更新 K8s Secret ───
update_k8s_secret
echo ""

# ─── Step 4: 切換 IDE token ───
token_switched=false
if switch_token "$target" "$current"; then
    token_switched=true
fi
echo ""

# ─── Step 5: 提示手動步驟 or 重啟 ───
if [ "$token_switched" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 接下來："
    echo "  1. 重啟 Kiro IDE（關閉再開啟）"
    echo "  2. 確認右下角帳號顯示為 ${ACCOUNTS[$((target - 1))]}"
    echo "  3. 重啟 agent pod："
    echo "     ./scripts/switch-kiro-account.sh --start"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 首次設定帳號 ${target}，請："
    echo "  1. 在 Kiro IDE sign out"
    echo "  2. 用 ${ACCOUNTS[$((target - 1))]} 帳號登入"
    echo "  3. 登入後執行："
    echo "     cp ~/.aws/sso/cache/kiro-auth-token.json ~/.aws/sso/cache/kiro-auth-token-${target}.json"
    echo "  4. 重啟 agent pod："
    echo "     ./scripts/switch-kiro-account.sh --start"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
