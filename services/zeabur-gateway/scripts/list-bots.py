#!/usr/bin/env python3
"""列出所有 wecom bot 設定（可被 admin 直接 import 重用）。"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "services" / "zeabur-gateway"))

from lib import BotRegistry  # noqa: E402


def main() -> int:
    registry = BotRegistry.load(REPO_ROOT / "services" / "zeabur-gateway" / "bots")

    if not registry.bots:
        print("No bots configured. Add a YAML in services/zeabur-gateway/bots/")
        return 0

    print(f"{'Bot':<20} {'Domain':<25} {'Agent':<25} {'Enabled':<8}")
    print("─" * 80)
    for bot in registry.bots:
        print(
            f"{bot.name:<20} {bot.domain:<25} {bot.agent:<25} "
            f"{'✅' if bot.enabled else '⏸':<8}"
        )

    print()
    print(f"Total: {len(registry.bots)} bot(s), "
          f"{sum(1 for _ in registry.enabled())} enabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
