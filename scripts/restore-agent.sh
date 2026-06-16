#!/bin/bash
# ============================================================
# 角色狀態還原腳本
# 用途：從 NAS 備份還原指定角色的運行狀態
# 用法：
#   sudo bash scripts/restore-agent.sh <group/agent> [timestamp]
#   sudo bash scripts/restore-agent.sh bob                    # 比奇堡角色
#   sudo bash scripts/restore-agent.sh keding-dc/captain      # 科定DC角色
#   sudo bash scripts/restore-agent.sh bob 20260616_1400      # 指定時間點
#   sudo bash scripts/restore-agent.sh --list bob             # 列出可用備份
#   sudo bash scripts/restore-agent.sh --all                  # 全體還原（災難恢復）
# ============================================================

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/home/kdprogramer/Projects/bikini-bottom}"
NAS_BACKUP_BASE="/mnt/nas/backups/agents"
NAMESPACE="bikini-bottom"

# ─── 函數 ───────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

usage() {
    cat <<EOF
用法：
  sudo bash $0 <agent>                    還原比奇堡角色（最新備份）
  sudo bash $0 <group/agent>              還原指定群組角色
  sudo bash $0 <agent> <timestamp>        還原指定時間點（如 20260616_1400）
  sudo bash $0 --list <agent>             列出角色的所有可用備份
  sudo bash $0 --all                      災難恢復：還原全部角色
  sudo bash $0 --env [timestamp]          還原 .env 檔案

範例：
  sudo bash $0 bob
  sudo bash $0 keding-dc/captain
  sudo bash $0 bob 20260616_1400
  sudo bash $0 --list sandy
  sudo bash $0 --all
EOF
    exit 1
}

# 解析 group/agent 並返回：GROUP AGENT AGENT_DIR DEPLOYMENT_NAME
parse_agent() {
    local input="$1"
    local group agent agent_dir deploy_name

    if [[ "$input" == */* ]]; then
        group=$(dirname "$input")
        agent=$(basename "$input")
        agent_dir="$REPO_ROOT/agents/$group/$agent"
        deploy_name="${group}-${agent}"
    else
        group="bikini-bottom"
        agent="$input"
        agent_dir="$REPO_ROOT/agents/$agent"
        deploy_name="$agent"
    fi

    echo "$group|$agent|$agent_dir|$deploy_name"
}

# 找到備份檔案
find_backup() {
    local group="$1"
    local agent="$2"
    local timestamp="${3:-}"
    local backup_dir="$NAS_BACKUP_BASE/$group/$agent"

    if [ ! -d "$backup_dir" ]; then
        echo ""
        return
    fi

    if [ -n "$timestamp" ]; then
        # 指定時間點：優先找 full，其次 hourly
        local full="$backup_dir/${timestamp}_full.tar.gz"
        local hourly="$backup_dir/${timestamp}.tar.gz"
        if [ -f "$full" ]; then
            echo "$full"
        elif [ -f "$hourly" ]; then
            echo "$hourly"
        else
            echo ""
        fi
    else
        # 最新：優先找 full（如果在最近 24 小時內），否則最新的任何備份
        local latest_full=$(ls -1t "$backup_dir"/*_full.tar.gz 2>/dev/null | head -1)
        local latest_any=$(ls -1t "$backup_dir"/*.tar.gz 2>/dev/null | head -1)

        if [ -n "$latest_full" ]; then
            echo "$latest_full"
        elif [ -n "$latest_any" ]; then
            echo "$latest_any"
        else
            echo ""
        fi
    fi
}

# 列出可用備份
list_backups() {
    local input="$1"
    IFS='|' read -r group agent agent_dir deploy_name <<< "$(parse_agent "$input")"
    local backup_dir="$NAS_BACKUP_BASE/$group/$agent"

    if [ ! -d "$backup_dir" ]; then
        log "❌ 找不到 $input 的備份目錄: $backup_dir"
        exit 1
    fi

    echo ""
    echo "=== $input 的可用備份 ==="
    echo "目錄: $backup_dir"
    echo ""
    ls -lht "$backup_dir"/*.tar.gz 2>/dev/null || echo "（無備份）"
    echo ""
    echo "備份數量: $(ls "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)"
}

# 還原單一角色
restore_agent() {
    local input="$1"
    local timestamp="${2:-}"

    IFS='|' read -r group agent agent_dir deploy_name <<< "$(parse_agent "$input")"

    log "=== 還原 $input ==="
    log "Agent 目錄: $agent_dir"
    log "Deployment: $deploy_name"

    # 確認 agent 目錄存在
    if [ ! -d "$agent_dir" ]; then
        log "⚠️  Agent 目錄不存在，建立中: $agent_dir"
        mkdir -p "$agent_dir"
    fi

    # 找到備份
    local backup=$(find_backup "$group" "$agent" "$timestamp")
    if [ -z "$backup" ]; then
        log "❌ 找不到 $input 的備份檔案"
        if [ -n "$timestamp" ]; then
            log "   嘗試的時間點: $timestamp"
            log "   使用 --list $input 查看可用備份"
        fi
        return 1
    fi

    log "使用備份: $backup"
    local size=$(du -sh "$backup" | cut -f1)
    log "檔案大小: $size"

    # 驗證備份完整性
    if ! tar -tzf "$backup" >/dev/null 2>&1; then
        log "❌ 備份檔案損壞: $backup"
        return 1
    fi

    # 解壓到暫存目錄
    local staging="/tmp/restore-${group}-${agent}-$$"
    rm -rf "$staging"
    mkdir -p "$staging"
    tar -xzf "$backup" -C "$staging"

    log "備份內容:"
    find "$staging" -type f | sed "s|$staging/|  |" | head -20

    # 還原檔案（不刪除 agent 目錄中的其他檔案）
    echo ""
    log "正在還原到 $agent_dir ..."

    # 用 rsync 合併（不刪除目標中的其他檔案）
    rsync -a --backup --suffix=".pre-restore" "$staging/" "$agent_dir/"

    # 修正權限（容器內 user = twkder, uid=1000）
    local twkder_uid=$(id -u twkder 2>/dev/null || echo "1000")
    local twkder_gid=$(id -g twkder 2>/dev/null || echo "1000")
    chown -R "$twkder_uid:$twkder_gid" "$agent_dir/.openab" 2>/dev/null || true
    chown -R "$twkder_uid:$twkder_gid" "$agent_dir/.local" 2>/dev/null || true
    chown -R "$twkder_uid:$twkder_gid" "$agent_dir/.semantic_search" 2>/dev/null || true
    chown -R "$twkder_uid:$twkder_gid" "$agent_dir/.kiro/steering/memory.md" 2>/dev/null || true

    # 清理暫存
    rm -rf "$staging"

    # 重啟 pod
    log "重啟 deployment: $deploy_name"
    if kubectl rollout restart deployment "$deploy_name" -n "$NAMESPACE" 2>/dev/null; then
        log "✅ $input 還原完成，pod 重啟中"
    else
        log "⚠️  $input 檔案還原完成，但 kubectl restart 失敗（可能 deployment 名稱不同）"
        log "   請手動重啟: kubectl rollout restart deployment <name> -n $NAMESPACE"
    fi
}

# 還原 .env
restore_env() {
    local timestamp="${1:-}"
    local env_dir="$NAS_BACKUP_BASE/env"
    local backup_file

    if [ -n "$timestamp" ]; then
        backup_file="$env_dir/${timestamp}.env.gpg"
        [ ! -f "$backup_file" ] && backup_file="$env_dir/${timestamp}.env"
    else
        backup_file=$(ls -1t "$env_dir"/*.env.gpg 2>/dev/null | head -1)
        [ -z "$backup_file" ] && backup_file=$(ls -1t "$env_dir"/*.env 2>/dev/null | head -1)
    fi

    if [ -z "$backup_file" ] || [ ! -f "$backup_file" ]; then
        log "❌ 找不到 .env 備份"
        exit 1
    fi

    log "還原 .env from: $backup_file"

    # 備份現有 .env
    if [ -f "$REPO_ROOT/.env" ]; then
        cp "$REPO_ROOT/.env" "$REPO_ROOT/.env.pre-restore"
        log "現有 .env 已備份為 .env.pre-restore"
    fi

    if [[ "$backup_file" == *.gpg ]]; then
        BACKUP_PASSPHRASE="${BACKUP_PASSPHRASE:-bikini-bottom-backup-2026}"
        gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" --decrypt -o "$REPO_ROOT/.env" "$backup_file"
    else
        cp "$backup_file" "$REPO_ROOT/.env"
    fi

    log "✅ .env 還原完成"
}

# 全體還原
restore_all() {
    log "=== 災難恢復：還原所有角色 ==="
    echo ""
    echo "⚠️  這將覆蓋所有角色的 runtime 資料"
    echo "   按 Ctrl+C 取消，或按 Enter 繼續..."
    read -r

    local all_agents=(
        "bob" "patrick" "puff" "squidward" "sandy"
        "pearl" "larry" "mermaid-man" "conch" "gary"
        "keding-dc/captain" "keding-dc/ironman"
        "keding-dc/strange" "keding-dc/order-transform"
        "keding-wecom/order-transform"
    )

    local success=0
    local failed=0

    for agent in "${all_agents[@]}"; do
        if restore_agent "$agent"; then
            success=$((success + 1))
        else
            failed=$((failed + 1))
        fi
        echo ""
    done

    # 還原 .env
    restore_env

    log "=== 全體還原完成: $success 成功, $failed 失敗 ==="
}

# ─── 主入口 ─────────────────────────────────────────────────

if [ $# -eq 0 ]; then
    usage
fi

case "$1" in
    --list)
        [ $# -lt 2 ] && usage
        list_backups "$2"
        ;;
    --all)
        restore_all
        ;;
    --env)
        restore_env "${2:-}"
        ;;
    --help|-h)
        usage
        ;;
    *)
        restore_agent "$1" "${2:-}"
        ;;
esac
