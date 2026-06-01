#!/bin/bash
# 刪除蟹堡王頻道中所有包含 "Cron" 的訊息（非討論串）
# 使用小蝸(Gary)的 bot token
#
# Rate limit 策略（根據 Discord 官方文件）：
# - DELETE message per-route limit: ~5 req / 5 sec (1 req/sec)
# - Global limit: 50 req/sec
# - 遇到 429 時讀取 retry_after 欄位等待

BOT_TOKEN="${DISCORD_BOT_TOKEN_GARY:?請設定 DISCORD_BOT_TOKEN_GARY 環境變數}"
CHANNEL_ID="1492090122257170526"

echo "=== 刪除 Cron 訊息腳本 ==="
echo "頻道: $CHANNEL_ID"
echo "關鍵字: Cron (不分大小寫)"
echo "Rate limit: 1 req/sec + retry_after handling"
echo ""

TOTAL_DELETED=0
TOTAL_FAILED=0
PASS=0
BEFORE_ID=""

while true; do
  PASS=$((PASS + 1))
  
  # 構建 URL（支援分頁）
  URL="https://discord.com/api/v10/channels/$CHANNEL_ID/messages?limit=100"
  if [ -n "$BEFORE_ID" ]; then
    URL="${URL}&before=${BEFORE_ID}"
  fi
  
  echo "[Pass $PASS] 取得訊息 (before=$BEFORE_ID)..."
  
  MESSAGES=$(curl -s "$URL" -H "Authorization: Bot $BOT_TOKEN")
  
  # 用 python 篩選並取得最後一則的 ID（用於分頁）
  RESULT=$(echo "$MESSAGES" | python3 -c "
import json, sys
msgs = json.load(sys.stdin)
if not isinstance(msgs, list) or len(msgs) == 0:
    print('EMPTY')
    sys.exit(0)

cron_ids = []
last_id = msgs[-1]['id']

for m in msgs:
    content = m.get('content', '').lower()
    if 'cron' in content:
        cron_ids.append(m['id'])

# 輸出格式: LAST_ID|id1,id2,id3...
if cron_ids:
    print(f'{last_id}|{\",\".join(cron_ids)}')
else:
    print(f'{last_id}|NONE')
")

  if [ "$RESULT" == "EMPTY" ]; then
    echo "  已到達頻道底部，沒有更多訊息。"
    break
  fi
  
  # 解析結果
  LAST_ID=$(echo "$RESULT" | cut -d'|' -f1)
  IDS_STR=$(echo "$RESULT" | cut -d'|' -f2)
  
  BEFORE_ID="$LAST_ID"
  
  if [ "$IDS_STR" == "NONE" ]; then
    echo "  本批 100 則中無 Cron 訊息，繼續往前翻..."
    sleep 0.5
    continue
  fi
  
  # 分割 ID
  IFS=',' read -ra IDS <<< "$IDS_STR"
  echo "  找到 ${#IDS[@]} 則 Cron 訊息，開始刪除..."
  
  for MID in "${IDS[@]}"; do
    if [[ -z "$MID" ]]; then continue; fi
    
    # 刪除訊息，捕獲完整 response header
    RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
      "https://discord.com/api/v10/channels/$CHANNEL_ID/messages/$MID" \
      -H "Authorization: Bot $BOT_TOKEN" \
      -D -)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)
    
    if [ "$HTTP_CODE" == "204" ]; then
      TOTAL_DELETED=$((TOTAL_DELETED + 1))
    elif [ "$HTTP_CODE" == "429" ]; then
      # 從 response body 取得 retry_after
      BODY=$(echo "$RESPONSE" | grep -A1 '{' | head -5)
      RETRY_AFTER=$(echo "$BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('retry_after', 5))
except:
    print(5)
" 2>/dev/null || echo "5")
      
      echo "  ⚠️ Rate limited, waiting ${RETRY_AFTER}s..."
      sleep "$RETRY_AFTER"
      
      # 重試
      RETRY_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
        "https://discord.com/api/v10/channels/$CHANNEL_ID/messages/$MID" \
        -H "Authorization: Bot $BOT_TOKEN")
      
      if [ "$RETRY_CODE" == "204" ]; then
        TOTAL_DELETED=$((TOTAL_DELETED + 1))
      else
        echo "  ❌ 重試失敗 $MID (HTTP $RETRY_CODE)"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
      fi
    else
      echo "  ❌ 刪除失敗 $MID (HTTP $HTTP_CODE)"
      TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
    
    # 安全間隔：1 request per second（符合 per-route limit）
    sleep 1
  done
  
  echo "  ✅ Pass $PASS 完成，累計刪除: $TOTAL_DELETED"
  
  # 安全閥
  if [ $PASS -ge 200 ]; then
    echo "  ⚠️ 達到最大 pass 數，停止。"
    break
  fi
done

echo ""
echo "=== 完成 ==="
echo "✅ 成功刪除: $TOTAL_DELETED"
echo "❌ 失敗: $TOTAL_FAILED"
