#!/bin/bash
# 記憶體監控腳本 - 每小時記錄一次，保留 30 天
# 用法：加入 crontab -> 0 * * * * /home/kdprogramer/Projects/bikini-bottom/scripts/mem-monitor.sh

LOG_DIR="/home/kdprogramer/Projects/bikini-bottom/logs/mem-monitor"
mkdir -p "$LOG_DIR"

DATE=$(date '+%Y-%m-%d')
TIME=$(date '+%H:%M:%S')
LOG_FILE="$LOG_DIR/mem-${DATE}.csv"

# 寫 header（如果檔案不存在）
if [ ! -f "$LOG_FILE" ]; then
    echo "timestamp,mem_total_mb,mem_used_mb,mem_available_mb,mem_percent,swap_total_mb,swap_used_mb,swap_percent,k3s_pods_mb" > "$LOG_FILE"
fi

# 取得系統記憶體（MB）
read MEM_TOTAL MEM_USED MEM_AVAIL <<< $(free -m | awk '/^Mem:/ {print $2, $3, $7}')
read SWAP_TOTAL SWAP_USED <<< $(free -m | awk '/^置換：/ {print $2, $3}')

# 如果中文 locale 不一樣，fallback
if [ -z "$SWAP_TOTAL" ]; then
    read SWAP_TOTAL SWAP_USED <<< $(free -m | awk '/^Swap:/ {print $2, $3}')
fi

# 計算百分比
MEM_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($MEM_USED/$MEM_TOTAL)*100}")
if [ "$SWAP_TOTAL" -gt 0 ] 2>/dev/null; then
    SWAP_PERCENT=$(awk "BEGIN {printf \"%.1f\", ($SWAP_USED/$SWAP_TOTAL)*100}")
else
    SWAP_PERCENT="0.0"
fi

# 取得 k3s pods 總記憶體
K3S_PODS_MB=$(kubectl top pods -n bikini-bottom --no-headers 2>/dev/null | awk '{
    val=$3
    if (val ~ /Mi$/) { gsub(/Mi/,"",val); total+=val }
    else if (val ~ /Gi$/) { gsub(/Gi/,"",val); total+=val*1024 }
} END {printf "%d", total}')

if [ -z "$K3S_PODS_MB" ]; then
    K3S_PODS_MB="N/A"
fi

# 寫入
echo "${DATE} ${TIME},${MEM_TOTAL},${MEM_USED},${MEM_AVAIL},${MEM_PERCENT},${SWAP_TOTAL},${SWAP_USED},${SWAP_PERCENT},${K3S_PODS_MB}" >> "$LOG_FILE"

# 清理 30 天前的 log
find "$LOG_DIR" -name "mem-*.csv" -mtime +30 -delete
