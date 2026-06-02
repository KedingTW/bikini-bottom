#!/bin/bash
# sync-skills.sh — 從外部 repo 同步 skill 到 shared/skills/
# 使用方式（在 Windows 直接跑或 WSL 皆可）：
#   bash scripts/sync-skills.sh
# 依據 shared/skills/skills.json 的定義，clone/pull 外部 repo 並複製指定 skill
#
# 注意：git 操作使用 git.exe（Windows credential），其餘用 bash。
# 需要：jq（WSL: sudo apt install jq / Windows: choco install jq）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$ROOT_DIR/shared/skills"
MANIFEST="$SKILLS_DIR/skills.json"
CACHE_DIR="$ROOT_DIR/.skill-repos"

# 偵測 git：優先用 git.exe（有 Windows credential），fallback 到 git
if command -v git.exe &>/dev/null; then
    GIT="git.exe"
    # git.exe 需要 Windows 路徑，提供轉換函數
    to_git_path() {
        echo "$1" | sed 's|^/mnt/\([a-z]\)/|\1:/|' | sed 's|/|\\|g'
    }
elif command -v git &>/dev/null; then
    GIT="git"
    to_git_path() { echo "$1"; }
else
    echo "[sync-skills] ERROR: git not found"
    exit 1
fi

if [ ! -f "$MANIFEST" ]; then
    echo "[sync-skills] ERROR: $MANIFEST not found"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "[sync-skills] ERROR: jq is required. Install: sudo apt install jq"
    exit 1
fi

mkdir -p "$CACHE_DIR"

sources_count=$(jq '.sources | length' "$MANIFEST")
echo "[sync-skills] found $sources_count source(s) in manifest"
echo "[sync-skills] using: $GIT"

synced=0

for i in $(seq 0 $((sources_count - 1))); do
    repo=$(jq -r ".sources[$i].repo" "$MANIFEST")
    branch=$(jq -r ".sources[$i].branch // \"main\"" "$MANIFEST")
    skills_path=$(jq -r ".sources[$i].path // \".kiro/skills\"" "$MANIFEST")

    repo_name=$(basename "$repo" .git)
    repo_dir="$CACHE_DIR/$repo_name"

    echo ""
    echo "[sync-skills] --- $repo_name (branch: $branch) ---"

    # Clone 或 pull
    if [ -d "$repo_dir/.git" ]; then
        echo "[sync-skills] pulling latest..."
        $GIT -C "$(to_git_path "$repo_dir")" fetch origin "$branch" --quiet
        $GIT -C "$(to_git_path "$repo_dir")" checkout "$branch" --quiet 2>/dev/null || \
            $GIT -C "$(to_git_path "$repo_dir")" checkout -b "$branch" "origin/$branch" --quiet
        $GIT -C "$(to_git_path "$repo_dir")" reset --hard "origin/$branch" --quiet
    else
        echo "[sync-skills] cloning..."
        $GIT clone --branch "$branch" --single-branch --depth 1 "$repo" "$(to_git_path "$repo_dir")" --quiet
    fi

    # 複製指定的 skill
    skills_list=$(jq -r ".sources[$i].skills[]" "$MANIFEST")
    for skill in $skills_list; do
        src="$repo_dir/$skills_path/$skill"
        dest="$SKILLS_DIR/$skill"

        if [ ! -d "$src" ] || [ ! -f "$src/SKILL.md" ]; then
            echo "[sync-skills] WARNING: skill '$skill' not found at $src"
            continue
        fi

        rm -rf "$dest"
        cp -r "$src" "$dest"
        synced=$((synced + 1))
        echo "[sync-skills] synced: $skill"
    done
done

echo ""
echo "[sync-skills] done: $synced skill(s) synced"
