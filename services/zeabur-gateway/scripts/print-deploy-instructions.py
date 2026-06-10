#!/usr/bin/env python3
"""
印出指定 bot 的 Zeabur 手動部署指引（暫用，等 ZeaburClient API 補完後改自動）。

每個 bot 包含：
- Zeabur service 設定（image、port、domain）
- 環境變數清單（從 .env 讀對應 ORDER_TRANSFORM_WECOM_* 等）
- WeCom 後台填的 callback URL

用法：
    python services/zeabur-gateway/scripts/print-deploy-instructions.py order-transform
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "zeabur-gateway"))

from lib import BotRegistry  # noqa: E402

GATEWAY_IMAGE = "ghcr.io/openabdev/openab-gateway:latest"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bot", help="bot name（如 order）")
    args = parser.parse_args()

    registry = BotRegistry.load(REPO_ROOT / "services" / "zeabur-gateway" / "bots")
    bot = registry.by_name(args.bot)

    print(f"# Zeabur 部署指引 — {bot.display_name} ({bot.name})\n")
    print("## 1. Zeabur Dashboard\n")
    print("- Project: bikini-bottom（若無則建立）")
    print(f"- 新增 Service：")
    print(f"  - Name: `{bot.zeabur_service_name}`")
    print(f"  - Source: Prebuilt Image")
    print(f"  - Image: `{GATEWAY_IMAGE}`")
    print(f"  - Exposed Port: 8080")
    print()
    print("## 2. Environment Variables（在 Zeabur service Variables 分頁設定）\n")
    print("| Gateway 內變數名 | 值（從本地 .env 複製） |")
    print("|-----------------|----------------------|")
    for gateway_var, env_var in bot.env_var_names().items():
        print(f"| `{gateway_var}` | 對應 `.env` 中的 `{env_var}` |")
    print()
    print("> 也可以填一個額外的 `GATEWAY_WS_TOKEN` 做 WS 連線認證，")
    print("> 然後在地端 `agents/{}/config.toml` 的 `[gateway]` 加 `auth_token = \"...\"`。".format(bot.agent))
    print()
    print("## 3. Domain\n")
    print(f"- Zeabur 預設 domain: `{bot.zeabur_service_name}.xxx.zeabur.app`（部署完才看得到）")
    print(f"- 自家 domain：在 DNS 加 CNAME：")
    print(f"  ```")
    print(f"  {bot.domain}.  CNAME  <Zeabur 給的 domain>")
    print(f"  ```")
    print(f"- 在 Zeabur service Domains 分頁加入 `{bot.domain}` 並等 SSL 簽發完成")
    print()
    print("## 4. WeCom 後台\n")
    print("- 應用 → 接收消息 → 設置 API 接收：")
    print(f"  - URL: `{bot.webhook_url}`")
    print(f"  - Token: 對應 `.env` 中的 `{bot.env_var_prefix}_WECOM_TOKEN`")
    print(f"  - EncodingAESKey: 對應 `.env` 中的 `{bot.env_var_prefix}_WECOM_ENCODING_AES_KEY`")
    print("- 點「保存」，Zeabur gateway 會自動回應驗證")
    print()
    print("## 5. 地端 wecom-bot 部署\n")
    print(f"- agent 目錄：`agents/{bot.agent}/`")
    print(f"- 確認 `agents/{bot.agent}/config.toml` 的 `gateway.url = \"{bot.ws_url}\"`")
    print(f"- 部署：`kubectl apply -f k3s/deployments/{bot.agent}.yaml`")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
