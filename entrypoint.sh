#!/bin/sh
# entrypoint.sh — 容器啟動前置作業
# 環境變數傳遞已由 OpenAB config.toml 的 inherit_env 處理，
# 此處僅保留 gh CLI 認證的持久化設定（作為 fallback）。

# 持久化 gh 認證 — 讓 gh 在非 kiro-cli 環境下也能使用（如 docker exec）
if [ -n "$GH_TOKEN" ]; then
  mkdir -p /home/agent/.config/gh
  printf "github.com:\n    oauth_token: %s\n    user: \n    git_protocol: https\n" "$GH_TOKEN" > /home/agent/.config/gh/hosts.yml
fi

# 執行傳入的 CMD
exec "$@"
