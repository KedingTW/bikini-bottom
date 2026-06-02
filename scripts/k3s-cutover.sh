#!/bin/bash
# 🏝️ 比奇堡 K3s 切換腳本
# 前提：舊機已執行 docker compose down
# 用法: bash scripts/k3s-cutover.sh

set -e

NAMESPACE="bikini-bottom"

echo "🏝️ 比奇堡 K3s 切換"
echo "==================="
echo ""
echo "⚠️  請確認舊機已執行: docker compose down"
read -p "   舊機已停止？(y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "取消。請先在舊機停止服務。"
  exit 0
fi

echo ""
echo "🚀 啟動所有 Deployment..."
kubectl scale deployment --all -n $NAMESPACE --replicas=1

echo ""
echo "⏳ 等待所有 Pod 就緒..."
kubectl wait --for=condition=ready pod --all -n $NAMESPACE --timeout=120s 2>/dev/null || true

echo ""
echo "📊 Pod 狀態："
kubectl get pods -n $NAMESPACE

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 檢查有沒有不正常的 Pod
NOT_READY=$(kubectl get pods -n $NAMESPACE --no-headers | grep -v "Running" | grep -v "Completed" || true)
if [ -z "$NOT_READY" ]; then
  echo "✅ 所有 Pod 正常運行！"
  echo ""
  echo "驗證步驟："
  echo "  1. 到 Discord mention 任一 bot 確認回應"
  echo "  2. kubectl logs -f deployment/bob -n $NAMESPACE"
  echo ""
  echo "如果有問題，Rollback："
  echo "  kubectl scale deployment --all -n $NAMESPACE --replicas=0"
  echo "  然後在舊機: docker compose up -d"
else
  echo "⚠️  有 Pod 尚未就緒："
  echo "$NOT_READY"
  echo ""
  echo "排查："
  echo "  kubectl describe pod <pod-name> -n $NAMESPACE"
  echo "  kubectl logs <pod-name> -n $NAMESPACE"
  echo ""
  echo "Rollback："
  echo "  kubectl scale deployment --all -n $NAMESPACE --replicas=0"
  echo "  然後在舊機: docker compose up -d"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
