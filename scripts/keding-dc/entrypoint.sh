#!/bin/bash
# Minimal entrypoint for keding-dc / keding-wecom bots
# 不做 NAS symlink、不做 shared steering/skills link
# 只處理 host.docker.internal + 降權啟動 OpenAB

# --- host.docker.internal for K3s (hostNetwork mode) ---
if ! grep -q "host.docker.internal" /etc/hosts 2>/dev/null; then
    echo "127.0.0.1 host.docker.internal" >> /etc/hosts
fi

# --- Drop privileges and start OpenAB ---
exec setpriv --reuid=agent --regid=agent --init-groups openab "$@"
