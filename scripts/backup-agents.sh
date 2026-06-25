#!/bin/bash
# ============================================================
# 角色狀態備份腳本
# 用途：備份所有 agent 的關鍵運行狀態到 NAS
# 排程：host crontab 每小時執行
# 用法：sudo bash scripts/backup-agents.sh [--mode hourly|full]
# ============================================================

set -euo pipefail

# ─── 設定 ───────────────────────────────────────────────────
REPO_ROOT="${REPO_ROOT:-/home/kdprogramer/Projects/bikini-bottom}"
NAS_BACKUP_BASE="/mnt/nas/backups/agents"
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
BACKUP_FILES=(
    ".openab/thread_map.json"
    ".openab/cronjob.toml"
    ".kiro/steering/memory.md"
)

# 備份目錄（含子目錄內容）
BACKUP_DIRS=(
    ".local/share/kiro-cli"
)

# full 模式額外備份
FULL_DIRS=(
    ".semantic_search/models"
)

# 排除的大型檔案模式（僅用於 .local/share/kiro-cli 備份時）
EXCLUDE_PATTERNS=(
    "*.safetensors"
    "*.onnx"
    "*.bin"
)

# ─── 函數 ───────────────────────────────────────────────────

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# 確認備份目錄可用（NAS 或 fallback）
resolve_backup_dir() {
    if mountpoint -q /mnt/nas 2>/dev/null && [ -d "$NAS_BACKUP_BASE" ]; then
        # 寫入測試
        if touch "$NAS_BACKUP_BASE/.write-test" 2>/dev/null; then
            rm -f "$NAS_BACKUP_BASE/.write-test"
            echo "$NAS_BACKUP_BASE"
            return 0
        fi
    fi
    log "⚠️  NAS 不可用，使用 fallback: $FALLBACK_BASE"
    mkdir -p "$FALLBACK_BASE"
    echo "$FALLBACK_BASE"
}

# 取得 agent 在 host 上的實際目錄
get_agent_dir() {
    local group_agent="$1"
    local group=$(dirname "$group_agent")
    local agent=$(basename "$group_agent")

    if [ "$group" = "bikini-bottom" ]; then
        echo "$REPO_ROOT/agents/$agent"
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

    # 建立暫存目錄
    rm -rf "$STAGING"
    mkdir -p "$STAGING"

    HAS_FILES=0

    # 複製關鍵檔案
    for f in "${BACKUP_FILES[@]}"; do
        if [ -f "$AGENT_DIR/$f" ]; then
            mkdir -p "$STAGING/$(dirname "$f")"
            cp -a "$AGENT_DIR/$f" "$STAGING/$f" 2>/dev/null && HAS_FILES=1
        fi
    done

    # 複製關鍵目錄（排除模型檔）
    for d in "${BACKUP_DIRS[@]}"; do
        if [ -d "$AGENT_DIR/$d" ]; then
            mkdir -p "$STAGING/$d"
            EXCLUDES=""
            for pattern in "${EXCLUDE_PATTERNS[@]}"; do
                EXCLUDES="$EXCLUDES --exclude=$pattern"
            done
            rsync -a $EXCLUDES "$AGENT_DIR/$d/" "$STAGING/$d/" 2>/dev/null && HAS_FILES=1
        fi
    done

    # SQLite 特殊處理：覆蓋 rsync 的 copy 用安全版本
    SQLITE_SRC="$AGENT_DIR/.local/share/kiro-cli/data.sqlite3"
    SQLITE_DST="$STAGING/.local/share/kiro-cli/data.sqlite3"
    if [ -f "$SQLITE_SRC" ]; then
        mkdir -p "$(dirname "$SQLITE_DST")"
        safe_copy_sqlite "$SQLITE_SRC" "$SQLITE_DST"
        # WAL/SHM
        for ext in "-wal" "-shm"; do
            [ -f "${SQLITE_SRC}${ext}" ] && cp -a "${SQLITE_SRC}${ext}" "${SQLITE_DST}${ext}" 2>/dev/null
        done
        HAS_FILES=1
    fi

    # full 模式：額外備份 semantic_search/models
    if [ "$MODE" = "full" ]; then
        for d in "${FULL_DIRS[@]}"; do
            if [ -d "$AGENT_DIR/$d" ]; then
                mkdir -p "$STAGING/$d"
                rsync -a "$AGENT_DIR/$d/" "$STAGING/$d/" 2>/dev/null && HAS_FILES=1
            fi
        done
    fi

    # 如果沒有任何檔案可備份，跳過
    if [ "$HAS_FILES" -eq 0 ]; then
        log "[SKIP] $group_agent: no backup-worthy files"
        rm -rf "$STAGING"
        continue
    fi

    # 壓縮到 NAS
    ARCHIVE_DIR="$DEST/$GROUP/$AGENT"
    mkdir -p "$ARCHIVE_DIR"

    if [ "$MODE" = "full" ]; then
        ARCHIVE="$ARCHIVE_DIR/${DATE}_full.tar.gz"
    else
        ARCHIVE="$ARCHIVE_DIR/${DATE}.tar.gz"
    fi

    if tar -czf "$ARCHIVE" -C "$STAGING" . 2>/dev/null; then
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
    else
        log "[FAIL] $group_agent: tar creation failed"
        FAILED=$((FAILED + 1))
        FAILED_AGENTS+=("$group_agent")
    fi

    # 清理暫存
    rm -rf "$STAGING"
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
        # fallback: 直接 copy（NAS 已有權限管控）
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
