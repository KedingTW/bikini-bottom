#!/bin/bash
# 在容器啟動時，將 /shared/steering/ 的共用文件 symlink 到 agent 的 steering 目錄
# 用法：由 docker-compose entrypoint 呼叫，或手動執行

SHARED_DIR="/shared/steering"
STEERING_DIR="/home/agent/.kiro/steering"

if [ ! -d "$SHARED_DIR" ]; then
    echo "[link-shared-steering] $SHARED_DIR not found, skipping"
    exit 0
fi

mkdir -p "$STEERING_DIR"

for file in "$SHARED_DIR"/*.md; do
    [ -f "$file" ] || continue
    filename=$(basename "$file")
    target="$STEERING_DIR/$filename"
    # 如果已存在且不是 symlink，先備份
    if [ -f "$target" ] && [ ! -L "$target" ]; then
        mv "$target" "$target.bak"
    fi
    ln -sf "$file" "$target"
done

echo "[link-shared-steering] done: $(ls "$SHARED_DIR"/*.md 2>/dev/null | wc -l) files linked"
