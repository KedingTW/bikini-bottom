#!/usr/bin/env python3
"""
檢查 .env 是否包含所有 enabled bot 需要的密鑰。
未補齊的會印出來提醒使用者。

用法：
    python services/zeabur-gateway/scripts/check-env.py
    python services/zeabur-gateway/scripts/check-env.py --bot order
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "zeabur-gateway"))

from lib import BotRegistry  # noqa: E402


def load_dotenv(env_path: Path) -> dict[str, str]:
    """簡單 .env 解析器（不依賴外部套件）。"""
    result: dict[str, str] = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bot", help="只檢查指定 bot")
    parser.add_argument("--env", default=".env", help=".env 路徑（預設 .env）")
    args = parser.parse_args()

    env_path = REPO_ROOT / args.env
    env = load_dotenv(env_path)
    if not env:
        print(f"⚠️  {args.env} not found or empty", file=sys.stderr)

    registry = BotRegistry.load(REPO_ROOT / "services" / "zeabur-gateway" / "bots")

    bots = (
        [registry.by_name(args.bot)] if args.bot
        else list(registry.enabled())
    )

    if not bots:
        print("No enabled bots to check")
        return 0

    overall_ok = True
    for bot in bots:
        print(f"━━━ {bot.name} ({bot.display_name}) ━━━")
        missing = []
        for gateway_var, env_var in bot.env_var_names().items():
            value = env.get(env_var) or os.environ.get(env_var)
            status = "✅" if value else "❌"
            display = "(set)" if value else "(missing)"
            print(f"  {status} {env_var:<40} → gateway env: {gateway_var}  {display}")
            if not value:
                missing.append(env_var)
        if missing:
            overall_ok = False
            print(f"  ⚠️  Missing {len(missing)} var(s) in {args.env}")
        else:
            print("  All required vars present ✓")
        print()

    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
