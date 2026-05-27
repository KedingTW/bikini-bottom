#!/bin/bash
# 刪除蟹堡王頻道中所有 cron 排程產生的討論串
# 使用小蝸(Gary)的 bot token
# 操作：DELETE /channels/{thread_id}

BOT_TOKEN="${DISCORD_BOT_TOKEN_GARY:?請設定 DISCORD_BOT_TOKEN_GARY 環境變數}"
GUILD_ID="1492090122257170523"
CHANNEL_ID="1492090122257170526"

# 保留的 thread（不要刪除）
KEEP_THREADS="1507263412231475370"  # ★hsuan_AI快速生成教育訓練影片

echo "=== 刪除 Cron Threads 腳本 ==="
echo "頻道: $CHANNEL_ID"
echo ""

# Step 1: 取得所有 active threads
echo "[1/3] 取得 active threads..."
THREADS_JSON=$(curl -s -X GET \
  "https://discord.com/api/v10/guilds/$GUILD_ID/threads/active" \
  -H "Authorization: Bot $BOT_TOKEN")

# Step 2: 篩選目標頻道中「排程」開頭的 thread
echo "[2/3] 篩選排程相關 threads..."
THREAD_IDS=$(echo "$THREADS_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
keep = {'$KEEP_THREADS'}
threads = data.get('threads', [])
count = 0
for t in threads:
    if t.get('parent_id') == '$CHANNEL_ID':
        name = t.get('name', '')
        tid = t['id']
        if tid in keep:
            continue
        # 只刪除排程產生的 thread（排程D/E/A/B/C/Push/SqCheck）
        if '排程' in name or 'Cron' in name or 'cron' in name or 'SqCheck' in name:
            print(tid)
            count += 1
print(f'# 找到 {count} 個待刪除 thread', file=sys.stderr)
")

TOTAL=$(echo "$THREAD_IDS" | grep -cv '^$')
echo "找到 $TOTAL 個排程 thread 待刪除"
echo ""

# Step 3: 逐一刪除
echo "[3/3] 開始刪除..."
DONE=0
FAILED=0

for TID in $THREAD_IDS; do
  if [[ -z "$TID" ]]; then continue; fi
  
  RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    "https://discord.com/api/v10/channels/$TID" \
    -H "Authorization: Bot $BOT_TOKEN")
  
  if [ "$RESULT" == "200" ]; then
    DONE=$((DONE + 1))
  elif [ "$RESULT" == "429" ]; then
    # Rate limited, wait and retry
    echo "  ⚠️ Rate limited at #$DONE, waiting 5s..."
    sleep 5
    RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
      "https://discord.com/api/v10/channels/$TID" \
      -H "Authorization: Bot $BOT_TOKEN")
    if [ "$RESULT" == "200" ]; then
      DONE=$((DONE + 1))
    else
      echo "  ❌ 刪除失敗 $TID (HTTP $RESULT)"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "  ❌ 刪除失敗 $TID (HTTP $RESULT)"
    FAILED=$((FAILED + 1))
  fi
  
  # Progress every 50
  if [ $((DONE % 50)) -eq 0 ] && [ $DONE -gt 0 ]; then
    echo "  ✅ 進度: $DONE/$TOTAL (失敗: $FAILED)"
  fi
  
  # Rate limit protection: ~5 requests/sec
  sleep 0.2
done

echo ""
echo "=== 完成 ==="
echo "✅ 成功刪除: $DONE"
echo "❌ 失敗: $FAILED"
echo "📊 總計: $TOTAL"
