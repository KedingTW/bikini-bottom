#!/bin/bash
# Entrypoint for keding-dc / keding-wecom bots
# 與比奇堡相同管理方式：shared steering/skills link + thread_map 保護 + 降權

# --- host.docker.internal for K3s (hostNetwork mode) ---
if ! grep -q "host.docker.internal" /etc/hosts 2>/dev/null; then
    echo "127.0.0.1 host.docker.internal" >> /etc/hosts
fi

# --- Shared steering symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-steering.sh"

# --- Shared skills symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-skills.sh"

# --- Preserve thread_map across restarts ---
THREAD_MAP="/home/agent/.openab/thread_map.json"
THREAD_MAP_BAK="/home/agent/.openab/thread_map.json.bak"

if [ -f "$THREAD_MAP" ]; then
    cp "$THREAD_MAP" "$THREAD_MAP_BAK"
    echo "[thread-map] backed up ($(wc -c < "$THREAD_MAP") bytes)"
fi

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
    fi
) &

# --- Drop privileges and start OpenAB ---
exec setpriv --reuid=agent --regid=agent --init-groups openab "$@"
