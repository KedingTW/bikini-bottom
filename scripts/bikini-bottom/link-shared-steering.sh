#!/bin/bash
# Link shared steering files to agent's .kiro/steering directory
# 排除清單中的檔案不建 symlink（agent 需要時自行讀取 /opt/steering/xxx.md）

# 不需要每次 session 載入的檔案（節省 token，agent 透過 workflow 索引知道去哪讀）
EXCLUDE=(
    "stt-workflow.md"
    "shared-drive.md"
    "cronjob.md"
    "discord-roles.md"
    "channel-handoff.md"
)

# Try /opt/steering first (local bind mount), fallback to /shared/steering (NAS)
if [ -d "/opt/steering" ]; then
    SHARED_DIR="/opt/steering"
elif [ -d "/shared/steering" ]; then
    SHARED_DIR="/shared/steering"
else
    echo "[link-shared-steering] no steering source found, skipping"
    exit 0
fi

STEERING_DIR="/home/agent/.kiro/steering"
mkdir -p "$STEERING_DIR"

for file in "$SHARED_DIR"/*.md; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")

    # 跳過排除清單中的檔案
    skip=false
    for ex in "${EXCLUDE[@]}"; do
        if [ "$filename" = "$ex" ]; then
            skip=true
            break
        fi
    done
    if [ "$skip" = true ]; then
        continue
    fi

    target="$STEERING_DIR/$filename"
    if [ -f "$target" ] && [ ! -L "$target" ]; then
        mv "$target" "$target.bak"
    fi
    ln -sf "$file" "$target"
done

echo "[link-shared-steering] done: $(ls "$STEERING_DIR"/*.md 2>/dev/null | wc -l) files linked"
