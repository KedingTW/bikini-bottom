#!/bin/bash
# 🏝️ 從 bob.yaml 模板生成其他 agent 的 deployment YAML
# 用法: bash scripts/k3s-gen-deployments.sh

set -e

TEMPLATE="k3s/deployments/bob.yaml"
OUTPUT_DIR="k3s/deployments"

# 格式: name|secret_key|git_name|skills|extra_env
AGENTS=(
  "patrick|PATRICK|派大星 (Patrick)|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|"
  "puff|PUFF|puff [bot]|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|"
  "squidward|SQUIDWARD|章魚哥 (Squidward)|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|"
  "sandy|SANDY|珊迪 (Sandy)|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|RUST_LOG=openab=debug"
  "pearl|PEARL|pearl [bot]|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|"
  "larry|LARRY|蝦霸 (Larry)|xlsx,pdf,pptx,docx,doc-coauthoring,company-kb|"
  "conch|CONCH|神奇海螺 (Magic Conch)|company-kb|"
  "mermaid-man|MERMAID_MAN|海超人 (Mermaid Man)|company-kb|"
)

echo "🏝️ 生成 Agent Deployment YAML"
echo ""

for entry in "${AGENTS[@]}"; do
  IFS='|' read -r name secret_key git_name skills extra_env <<< "$entry"
  output="$OUTPUT_DIR/$name.yaml"
  
  sed \
    -e "s/bob/$name/g" \
    -e "s/BOB/$secret_key/g" \
    -e "s/海綿寶寶 (SpongeBob)/$git_name/g" \
    -e "s/xlsx,pdf,pptx,docx,doc-coauthoring,company-kb/$skills/g" \
    "$TEMPLATE" > "$output"
  
  # 如果沒有 RUST_LOG，移除該行
  if [ -z "$extra_env" ]; then
    sed -i '/RUST_LOG/,+1d' "$output"
  fi
  
  echo "  ✅ $output"
done

echo ""
echo "✅ 所有 Deployment 已生成！"
echo "   共 $(ls $OUTPUT_DIR/*.yaml | wc -l) 個檔案"
