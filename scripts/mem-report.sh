#!/bin/bash
# 記憶體使用報告 - 彙總最近 N 天的監控數據
# 用法：./mem-report.sh [天數，預設7]

DAYS=${1:-7}
LOG_DIR="/home/kdprogramer/Projects/bikini-bottom/logs/mem-monitor"

echo "============================================"
echo "  記憶體使用報告（最近 ${DAYS} 天）"
echo "  產生時間：$(date '+%Y-%m-%d %H:%M:%S')"
echo "  主機：$(hostname)"
echo "============================================"
echo ""

# 系統資訊
echo "## 硬體規格"
echo "- 實體記憶體：$(free -h | awk '/^Mem:/ {print $2}')"
echo "- Swap：$(free -h | tail -1 | awk '{print $2}')"
echo "- CPU：$(nproc) cores"
echo "- 磁碟：NVMe SSD ($(df -h / | awk 'NR==2 {print $2}'))"
echo ""

# 彙總統計
echo "## 記憶體使用統計（${DAYS} 天）"
echo ""
echo "| 指標 | 最小值 | 平均值 | 最大值 | 當前值 |"
echo "|------|--------|--------|--------|--------|"

# 收集所有數據
ALL_DATA=""
for i in $(seq 0 $((DAYS-1))); do
    D=$(date -d "${i} days ago" '+%Y-%m-%d')
    FILE="$LOG_DIR/mem-${D}.csv"
    if [ -f "$FILE" ]; then
        ALL_DATA+=$(tail -n +2 "$FILE")
        ALL_DATA+=$'\n'
    fi
done

if [ -z "$ALL_DATA" ]; then
    echo "（尚無足夠資料，請等待至少 24 小時）"
else
    # 記憶體使用率
    echo "$ALL_DATA" | awk -F',' '
    NF>=5 && $5+0>0 {
        if (NR==1 || $5+0 < min_mem) min_mem=$5+0
        if ($5+0 > max_mem) max_mem=$5+0
        sum_mem+=$5+0
        count++
        last_mem=$5+0
    }
    END {
        if (count>0) printf "| RAM 使用率(%%) | %.1f | %.1f | %.1f | %.1f |\n", min_mem, sum_mem/count, max_mem, last_mem
    }'

    # Swap 使用率
    echo "$ALL_DATA" | awk -F',' '
    NF>=8 && $8+0>=0 {
        if (NR==1 || $8+0 < min_swap) min_swap=$8+0
        if ($8+0 > max_swap) max_swap=$8+0
        sum_swap+=$8+0
        count++
        last_swap=$8+0
    }
    END {
        if (count>0) printf "| Swap 使用率(%%) | %.1f | %.1f | %.1f | %.1f |\n", min_swap, sum_swap/count, max_swap, last_swap
    }'

    # K3s pods 記憶體
    echo "$ALL_DATA" | awk -F',' '
    NF>=9 && $9+0>0 {
        val=$9+0
        if (NR==1 || val < min_k3s) min_k3s=val
        if (val > max_k3s) max_k3s=val
        sum_k3s+=val
        count++
        last_k3s=val
    }
    END {
        if (count>0) printf "| K3s Pods (MB) | %d | %d | %d | %d |\n", min_k3s, sum_k3s/count, max_k3s, last_k3s
    }'
fi

echo ""
echo "## 結論"
echo ""

# 取得當前數據
CURRENT_MEM_PCT=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2*100}')
CURRENT_SWAP_USED=$(free -m | tail -1 | awk '{print $3}')
MEM_USED_MB=$(free -m | awk '/^Mem:/ {print $3}')
MEM_TOTAL_MB=$(free -m | awk '/^Mem:/ {print $2}')
SWAP_TOTAL_MB=$(free -m | tail -1 | awk '{print $2}')

echo "- 當前 RAM 使用率：${CURRENT_MEM_PCT}%"
echo "- 當前 Swap 使用：${CURRENT_SWAP_USED} MB / ${SWAP_TOTAL_MB} MB"
echo ""

# 計算超過 80% 的時間佔比（核心指標）
if [ -n "$ALL_DATA" ]; then
    OVER80_STATS=$(echo "$ALL_DATA" | awk -F',' '
    NF>=5 && $5+0>0 {
        total++
        if ($5+0 >= 80) over80++
    }
    END {
        if (total>0) printf "%d %d %.1f", over80, total, (over80/total)*100
        else printf "0 0 0.0"
    }')
    OVER80_COUNT=$(echo "$OVER80_STATS" | awk '{print $1}')
    TOTAL_COUNT=$(echo "$OVER80_STATS" | awk '{print $2}')
    OVER80_PCT=$(echo "$OVER80_STATS" | awk '{print $3}')

    echo "## 📊 RAM ≥ 80% 持續時間分析"
    echo ""
    echo "- 監控資料筆數：${TOTAL_COUNT} 筆（每小時 1 筆）"
    echo "- RAM ≥ 80% 的筆數：${OVER80_COUNT} 筆"
    echo "- **RAM ≥ 80% 佔比：${OVER80_PCT}%**"
    echo ""

    if (( $(echo "$OVER80_PCT >= 70" | bc -l) )); then
        echo "🔴 RAM 使用率在 ${DAYS} 天監控期間，有 ${OVER80_PCT}% 的時間超過 80%。"
        echo "   結論：實體記憶體不足，建議升級至 64GB。"
    elif (( $(echo "$OVER80_PCT >= 40" | bc -l) )); then
        echo "🟡 RAM 使用率有 ${OVER80_PCT}% 的時間超過 80%，記憶體壓力偏高。"
        echo "   建議持續觀察，或考慮升級。"
    else
        echo "🟢 RAM 使用率大部分時間在 80% 以下（僅 ${OVER80_PCT}% 超過）。"
        echo "   目前尚不需要升級。"
    fi
else
    echo "（尚無歷史資料，請等待至少 24 小時後再次執行）"
fi

echo ""
echo "## 補充資訊"
echo ""
echo "- 判斷標準：RAM 使用率需長時間（≥70% 時間佔比）維持在 80% 以上才建議升級"
echo "- Swap 用途：做為安全緩衝，避免 OOM，不代表需要更多 RAM"
echo "- 監控資料保存在：${LOG_DIR}/"
echo "- 下次報告指令：./scripts/mem-report.sh 7"
