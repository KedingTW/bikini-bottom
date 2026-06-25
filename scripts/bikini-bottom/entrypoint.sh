#!/bin/bash
# Wrapper entrypoint (runs as root): shared symlink -> drop to agent -> OpenAB

# --- host.docker.internal for K3s (hostNetwork mode) ---
if ! grep -q "host.docker.internal" /etc/hosts 2>/dev/null; then
    echo "127.0.0.1 host.docker.internal" >> /etc/hosts
fi

# --- /shared symlink (kd-dev/shared -> /shared) ---
if [ -d "/mnt/kd-dev/shared" ]; then
    ln -sfn /mnt/kd-dev/shared /shared
    echo "[shared] /shared -> /mnt/kd-dev/shared"
fi

# --- Shared steering symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-steering.sh"

# --- Shared skills symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-skills.sh"

# --- Preserve thread_map across restarts ---
THREAD_MAP="/home/agent/.openab/thread_map.json"
THREAD_MAP_BAK="/home/agent/.openab/thread_map.json.bak"

# 備份：只要檔案存在就備份（不管是否為空）
if [ -f "$THREAD_MAP" ]; then
    cp "$THREAD_MAP" "$THREAD_MAP_BAK"
    echo "[thread-map] backed up ($(wc -c < "$THREAD_MAP") bytes)"
fi

# 恢復：等 OpenAB 啟動後合併（背景執行）
(
    sleep 8
    if [ -f "$THREAD_MAP_BAK" ]; then
        python3 -c "
import json, sys

bak_path = '$THREAD_MAP_BAK'
cur_path = '$THREAD_MAP'

try:
    bak = json.load(open(bak_path))
except:
    bak = {}

try:
    cur = json.load(open(cur_path))
except:
    cur = {}

merged = {**bak, **cur}
json.dump(merged, open(cur_path, 'w'))
print(f'[thread-map] restored {len(merged)} entries (bak={len(bak)}, new={len(cur)})')
" 2>&1 || echo "[thread-map] restore FAILED, keeping .bak"
        # 不刪除 .bak — 保留作為安全網
    fi
) &

# --- Drop privileges and start OpenAB ---
# 確保 agent 屬於 gid 1002（host 檔案 group），讓 supplementalGroups 生效
if ! grep -q "^kd:" /etc/group 2>/dev/null; then
    groupadd -g 1002 kd 2>/dev/null || true
fi
usermod -aG kd agent 2>/dev/null || true

exec setpriv --reuid=agent --regid=agent --init-groups openab "$@"
