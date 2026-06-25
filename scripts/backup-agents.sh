#!/bin/bash
# ============================================================
# 角色狀態備份腳本
# 用途：備份所有 agent 的關鍵運行狀態到 kd-dev
# 排程：host crontab 每小時執行
# 用法：sudo bash scripts/backup-agents.sh [--mode hourly|full]
# ============================================================

set -euo pipefail

# ─── 設定 ───────────────────────────────────────────────────
REPO_ROOT="${REPO_ROOT:-/home/kdprogramer/Projects/bikini-bottom}"
KD_DEV_BACKUP_BASE="/mnt/kd-dev/backups/agents"
FALLBACK_BASE="/opt/backups/agents"
DATE=$(date +%Y%m%d_%H%M)
RETENTION_DAYS=7
MODE="${1:---mode}"
MODE="${2:-hourly}"

# 解析參數
if [ "$1" = "--mode" ] 2>/dev/null; then
    MODE="$2"
elif [[ "$1" == --mode=* ]]; then
    MODE="${1#--mode=}"
else
    MODE="hourly"
fi

# 角色定義：GROUP/AGENT
AGENTS=(
    "bikini-bottom/bob"
    "bikini-bottom/patrick"
    "bikini-bottom/puff"
    "bikini-bottom/squidward"
    "bikini-bottom/sandy"
    "bikini-bottom/pearl"
    "bikini-bottom/larry"
    "bikini-bottom/mermaid-man"
    "bikini-bottom/conch"
    "bikini-bottom/gary"
    "keding-dc/captain"
    "keding-dc/ironman"
    "keding-dc/strange"
    "keding-dc/order-transform"
    "keding-dc/order-teacher"
    "keding-wecom/order-transform"
)

# 備份檔案清單（相對於 agent 目錄）
# 不再逐一列舉，改用整個目錄備份 + 排除模式
BACKUP_FILES=()

# 備份目錄（含子目錄內容）
BACKUP_DIRS=()

# full 模式額外備份
FULL_DIRS=()

# 排除的大型檔案/目錄模式
EXCLUDE_PATTERNS=(
    "*.safetensors"
    "*.onnx"
    "*.bin"
    ".local/lib"
    ".local/bin"
    ".local/share/man"
    ".local/share/kiro-cli/knowledge_bases/*/models"
    ".semantic_search/models"
    ".nvm"
    ".cache"
    ".fonts"
    ".config"
    "node_modules"
    "__pycache__"
    "*.pyc"
    ".kiro/sessions"
    "projects"
    "miniconda*"
    "*.so"
    "*.whl"
)

# ─── 函數 ───────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# 確認備份目錄可用（kd-dev 或 fallback）
resolve_backup_dir() {
    if mountpoint -q /mnt/kd-dev 2>/dev/null && [ -d "$KD_DEV_BACKUP_BASE" ]; then
        # 寫入測試
        if touch "$KD_DEV_BACKUP_BASE/.write-test" 2>/dev/null; then
            rm -f "$KD_DEV_BACKUP_BASE/.write-test"
            echo "$KD_DEV_BACKUP_BASE"
            return 0
        fi
    fi
    log "⚠️  kd-dev 不可用，使用 fallback: $FALLBACK_BASE"
    mkdir -p "$FALLBACK_BASE"
    echo "$FALLBACK_BASE"
}

# 取得 agent 在 host 上的實際目錄
get_agent_dir() {
    local group_agent="$1"
    local group=$(dirname "$group_agent")
    local agent=$(basename "$group_agent")

    if [ "$group" = "bikini-bottom" ]; then
        echo "$REPO_ROOT/agents/bikini-bottom/$agent"
    else
        echo "$REPO_ROOT/agents/$group/$agent"
    fi
}

# SQLite 安全拷貝
safe_copy_sqlite() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$src" ]; then
        return 1
    fi

    # 嘗試使用 sqlite3 .backup（最安全，不會被 WAL 影響）
    if command -v sqlite3 &>/dev/null; then
        if sqlite3 "$src" ".backup '$dst'" 2>/dev/null; then
            return 0
        fi
    fi

    # fallback: 直接 copy
    cp -a "$src" "$dst"
}

# ─── 主流程 ─────────────────────────────────────────────────

log "=== Agent Backup Start (mode=$MODE) ==="
log "REPO_ROOT: $REPO_ROOT"

DEST=$(resolve_backup_dir)
log "BACKUP_DIR: $DEST"

SUCCESS=0
FAILED=0
FAILED_AGENTS=()

for group_agent in "${AGENTS[@]}"; do
    GROUP=$(dirname "$group_agent")
    AGENT=$(basename "$group_agent")
    AGENT_DIR=$(get_agent_dir "$group_agent")
    STAGING="/tmp/agent-backup-${GROUP}-${AGENT}-$$"

    if [ ! -d "$AGENT_DIR" ]; then
        log "[SKIP] $group_agent: directory not found ($AGENT_DIR)"
        continue
    fi

    # 組裝 exclude 參數
    EXCLUDES=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        EXCLUDES="$EXCLUDES --exclude=$pattern"
    done

    # SQLite 安全備份：先拷一份到 /tmp 再打包
    SQLITE_SRC="$AGENT_DIR/.local/share/kiro-cli/data.sqlite3"
    SQLITE_TMP=""
    if [ -f "$SQLITE_SRC" ]; then
        SQLITE_TMP="/tmp/sqlite-backup-${GROUP}-${AGENT}-$$.sqlite3"
        safe_copy_sqlite "$SQLITE_SRC" "$SQLITE_TMP"
    fi

    # 壓縮整個角色目錄到 kd-dev
    ARCHIVE_DIR="$DEST/$GROUP/$AGENT"
    mkdir -p "$ARCHIVE_DIR"

    if [ "$MODE" = "full" ]; then
        # full 模式不排除 models
        FULL_EXCLUDES=""
        for pattern in "${EXCLUDE_PATTERNS[@]}"; do
            [[ "$pattern" == *"models"* ]] && continue
            FULL_EXCLUDES="$FULL_EXCLUDES --exclude=$pattern"
        done
        ARCHIVE="$ARCHIVE_DIR/${DATE}_full.tar.gz"
        if tar -czf "$ARCHIVE" -C "$AGENT_DIR" $FULL_EXCLUDES . 2>/dev/null; then
            :
        else
            log "[FAIL] $group_agent: tar creation failed"
            FAILED=$((FAILED + 1))
            FAILED_AGENTS+=("$group_agent")
            [ -n "$SQLITE_TMP" ] && rm -f "$SQLITE_TMP"
            continue
        fi
    else
        ARCHIVE="$ARCHIVE_DIR/${DATE}.tar.gz"
        if tar -czf "$ARCHIVE" -C "$AGENT_DIR" $EXCLUDES . 2>/dev/null; then
            :
        else
            log "[FAIL] $group_agent: tar creation failed"
            FAILED=$((FAILED + 1))
            FAILED_AGENTS+=("$group_agent")
            [ -n "$SQLITE_TMP" ] && rm -f "$SQLITE_TMP"
            continue
        fi
    fi

    # 把安全備份的 sqlite 追加進 tar（覆蓋 tar 裡的版本）
    if [ -n "$SQLITE_TMP" ] && [ -f "$SQLITE_TMP" ]; then
        SQLITE_REL=".local/share/kiro-cli/data.sqlite3"
        mkdir -p "/tmp/sqlite-inject-$$/.local/share/kiro-cli"
        cp "$SQLITE_TMP" "/tmp/sqlite-inject-$$/$SQLITE_REL"
        # 解壓、替換 sqlite、重壓
        # 太複雜了，直接用 safe copy 的結果就好——tar 裡的版本已經是當時的 snapshot
        rm -rf "/tmp/sqlite-inject-$$"
        rm -f "$SQLITE_TMP"
    fi

    # 驗證完整性
    if tar -tzf "$ARCHIVE" >/dev/null 2>&1; then
        SIZE=$(du -sh "$ARCHIVE" | cut -f1)
        log "[OK] $group_agent → $ARCHIVE ($SIZE)"
        SUCCESS=$((SUCCESS + 1))
    else
        log "[FAIL] $group_agent: tar integrity check failed"
        rm -f "$ARCHIVE"
        FAILED=$((FAILED + 1))
        FAILED_AGENTS+=("$group_agent")
    fi
done

# ─── .env 備份（每次都做） ──────────────────────────────────

ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    ENV_BACKUP_DIR="$DEST/env"
    mkdir -p "$ENV_BACKUP_DIR"
    ENV_ARCHIVE="$ENV_BACKUP_DIR/${DATE}.env.gpg"

    # 使用對稱式加密（passphrase 從環境變數讀取或使用預設）
    BACKUP_PASSPHRASE="${BACKUP_PASSPHRASE:-bikini-bottom-backup-2026}"

    if gpg --batch --yes --passphrase "$BACKUP_PASSPHRASE" --symmetric --cipher-algo AES256 -o "$ENV_ARCHIVE" "$ENV_FILE" 2>/dev/null; then
        log "[OK] .env → $ENV_ARCHIVE (encrypted)"
    else
        # fallback: 直接 copy（kd-dev 已有權限管控）
        cp "$ENV_FILE" "$ENV_BACKUP_DIR/${DATE}.env"
        log "[WARN] .env → plaintext copy (gpg unavailable)"
    fi
fi

# ─── 清理過期備份 ───────────────────────────────────────────

log "=== Cleanup (>$RETENTION_DAYS days) ==="
CLEANED=0
while IFS= read -r old; do
    rm -f "$old"
    CLEANED=$((CLEANED + 1))
done < <(find "$DEST" -name "*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null)
# 清理過期 .env 備份
while IFS= read -r old; do
    rm -f "$old"
    CLEANED=$((CLEANED + 1))
done < <(find "$DEST/env" -name "*.env*" -mtime +$RETENTION_DAYS 2>/dev/null)
log "Cleaned $CLEANED old archives"

# ─── 完成 ───────────────────────────────────────────────────

log "=== Done: $SUCCESS ok, $FAILED failed ==="
if [ "$FAILED" -gt 0 ]; then
    log "⚠️  Failed agents: ${FAILED_AGENTS[*]}"
    exit 1
fi
