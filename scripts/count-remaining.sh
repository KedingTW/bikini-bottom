#!/bin/bash
BOT_TOKEN="${DISCORD_BOT_TOKEN_GARY:?請設定 DISCORD_BOT_TOKEN_GARY 環境變數}"
GUILD_ID="1492090122257170523"
CHANNEL_ID="1492090122257170526"

curl -s "https://discord.com/api/v10/guilds/$GUILD_ID/threads/active" \
  -H "Authorization: Bot $BOT_TOKEN" | python3 -c "
import json, sys
data = json.load(sys.stdin)
threads = data.get('threads', [])
cron = [t for t in threads if t.get('parent_id') == '$CHANNEL_ID' and '排程' in t.get('name', '')]
other = [t for t in threads if t.get('parent_id') == '$CHANNEL_ID' and '排程' not in t.get('name', '')]
print(f'排程 thread 剩餘: {len(cron)}')
print(f'其他 thread: {len(other)}')
for t in other:
    print(f'  - {t[\"id\"]}: {t[\"name\"][:60]}')
"
