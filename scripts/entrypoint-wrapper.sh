#!/bin/bash
# Wrapper entrypoint (runs as root): NAS symlink -> drop to agent -> OpenAB

# --- host.docker.internal for K3s (hostNetwork mode) ---
if ! grep -q "host.docker.internal" /etc/hosts 2>/dev/null; then
    echo "127.0.0.1 host.docker.internal" >> /etc/hosts
fi

# --- NAS symlink ---
if [ -n "$AGENT_NAME" ] && [ -d "/nas/shared" ]; then
    ln -sfn /nas/shared /shared
    echo "[nas-link] /shared -> /nas/shared"

    if [ -d "/nas/agents/$AGENT_NAME/projects" ]; then
        rm -rf /home/agent/projects 2>/dev/null
        ln -sfn "/nas/agents/$AGENT_NAME/projects" /home/agent/projects
        echo "[nas-link] /home/agent/projects -> /nas/agents/$AGENT_NAME/projects"
    fi
fi

# --- Shared steering symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-steering.sh"

# --- Shared skills symlink (as agent) ---
su -s /bin/bash agent -c "/usr/local/bin/link-shared-skills.sh"

# --- Backup thread_map before OpenAB overwrites it ---
THREAD_MAP="/home/agent/.openab/thread_map.json"
THREAD_MAP_BAK="/home/agent/.openab/thread_map.json.bak"
if [ -f "$THREAD_MAP" ] && [ "$(python3 -c "import json; print(len(json.load(open('$THREAD_MAP'))))" 2>/dev/null)" != "0" ]; then
    cp "$THREAD_MAP" "$THREAD_MAP_BAK"
    echo "[thread-map] backed up $(python3 -c "import json; print(len(json.load(open('$THREAD_MAP_BAK'))))" 2>/dev/null) entries"
fi

# --- Restore thread_map after OpenAB starts (background) ---
(
    sleep 5
    if [ -f "$THREAD_MAP_BAK" ]; then
        # Merge: keep OpenAB's new entries + restore old ones
        python3 -c "
import json
bak = json.load(open('$THREAD_MAP_BAK'))
try:
    cur = json.load(open('$THREAD_MAP'))
except:
    cur = {}
merged = {**bak, **cur}
json.dump(merged, open('$THREAD_MAP', 'w'))
print(f'[thread-map] restored {len(merged)} entries (was {len(cur)})')
" 2>/dev/null
        rm -f "$THREAD_MAP_BAK"
    fi
) &

# --- Drop privileges and start OpenAB ---
exec setpriv --reuid=agent --regid=agent --init-groups openab "$@"
