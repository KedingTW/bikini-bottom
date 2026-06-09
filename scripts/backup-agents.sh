#!/bin/bash
# ============================================================
# 角色狀態備份腳本
# 用途：備份所有 agent 的關鍵運行狀態到 NAS
# 排程：host crontab 每日 03:00
# 用法：bash scripts/backup-agents.sh
# ============================================================

set -euo pipefail

# ─── 設定 ───────────────────────────────────────────────────
REPO_ROOT="${REPO_ROOT:-/home/kdprogramer/Projects/bikini-bottom}"
BACKUP_BASE="${BACKUP_BASE:-/nas/backups/agents}"
FALLBACK_BASE="/opt/backups/agents"
DATE=$(date +%Y%m%d)
RETENTION_DAYS=7

AGENTS=(bob patrick puff squidward sandy pearl larry mermaid-man conch wecom-bot)

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

# 排除的大型檔案模式
EXCLUDE_PATTERNS=(
    "*.safetensors"
    "*.onnx"
    "*.bin"
    "models/*/pytorch_model.bin"
)

# ─── 函數 ───────────────────────────────────────────────────

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# 確認備份目錄可用（NAS 或 fallback）
resolve_backup_dir() {
    if [ -d "$(dirname "$BACKUP_BASE")" ] && touch "$BACKUP_BASE/.write-test" 2>/dev/null; then
        rm -f "$BACKUP_BASE/.write-test"
        echo "$BACKUP_BASE"
    else
        log "⚠️  NAS 不可用，使用 fallback: $FALLBACK_BASE"
        mkdir -p "$FALLBACK_BASE"
        echo "$FALLBACK_BASE"
    fi
}

# SQLite 安全拷貝
safe_copy_sqlite() {
    local src="$1"
    local dst="$2"

    if [ ! -f "$src" ]; then
        return 1
    fi

    # 嘗試使用 sqlite3 .backup（最安全）
    if command -v sqlite3 &>/dev/null; then
        sqlite3 "$src" ".backup '$dst'" 2>/dev/null && return 0
    fi

    # fallback: 直接 copy（凌晨通常安全）
    cp -a "$src" "$dst"
}

# ─── 主流程 ─────────────────────────────────────────────────

log "=== Agent Backup Start ==="
log "REPO_ROOT: $REPO_ROOT"

DEST=$(resolve_backup_dir)
log "BACKUP_DIR: $DEST"

SUCCESS=0
FAILED=0

for agent in "${AGENTS[@]}"; do
    AGENT_DIR="$REPO_ROOT/agents/$agent"
    STAGING="/tmp/agent-backup-$agent-$DATE"

    if [ ! -d "$AGENT_DIR" ]; then
        log "[SKIP] $agent: directory not found"
        continue
    fi

    # 建立暫存目錄
    rm -rf "$STAGING"
    mkdir -p "$STAGING"

    # 複製關鍵檔案
    for f in "${BACKUP_FILES[@]}"; do
        if [ -f "$AGENT_DIR/$f" ]; then
            mkdir -p "$STAGING/$(dirname "$f")"
            cp -a "$AGENT_DIR/$f" "$STAGING/$f"
        fi
    done

    # 複製關鍵目錄（排除大型模型檔）
    for d in "${BACKUP_DIRS[@]}"; do
        if [ -d "$AGENT_DIR/$d" ]; then
            mkdir -p "$STAGING/$d"

            # 建立 rsync exclude 參數
            EXCLUDES=""
            for pattern in "${EXCLUDE_PATTERNS[@]}"; do
                EXCLUDES="$EXCLUDES --exclude=$pattern"
            done

            rsync -a $EXCLUDES "$AGENT_DIR/$d/" "$STAGING/$d/" 2>/dev/null || true
        fi
    done

    # SQLite 特殊處理：覆蓋 rsync 的 copy 用安全版本
    SQLITE_SRC="$AGENT_DIR/.local/share/kiro-cli/data.sqlite3"
    SQLITE_DST="$STAGING/.local/share/kiro-cli/data.sqlite3"
    if [ -f "$SQLITE_SRC" ]; then
        mkdir -p "$(dirname "$SQLITE_DST")"
        safe_copy_sqlite "$SQLITE_SRC" "$SQLITE_DST"

        # WAL/SHM（如果存在）
        for ext in "-wal" "-shm"; do
            if [ -f "${SQLITE_SRC}${ext}" ]; then
                cp -a "${SQLITE_SRC}${ext}" "${SQLITE_DST}${ext}"
            fi
        done
    fi

    # 壓縮
    ARCHIVE_DIR="$DEST/$agent"
    mkdir -p "$ARCHIVE_DIR"
    ARCHIVE="$ARCHIVE_DIR/$DATE.tar.gz"

    tar -czf "$ARCHIVE" -C "$STAGING" . 2>/dev/null

    # 記錄大小
    SIZE=$(du -sh "$ARCHIVE" | cut -f1)
    log "[OK] $agent → $ARCHIVE ($SIZE)"
    SUCCESS=$((SUCCESS + 1))

    # 清理暫存
    rm -rf "$STAGING"
done

# ─── 清理過期備份 ───────────────────────────────────────────

log "=== Cleanup (>$RETENTION_DAYS days) ==="
CLEANED=0
for agent in "${AGENTS[@]}"; do
    if [ -d "$DEST/$agent" ]; then
        while IFS= read -r old; do
            rm -f "$old"
            CLEANED=$((CLEANED + 1))
        done < <(find "$DEST/$agent" -name "*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null)
    fi
done
log "Cleaned $CLEANED old archives"

# ─── 完成 ───────────────────────────────────────────────────

log "=== Done: $SUCCESS ok, $FAILED failed ==="
