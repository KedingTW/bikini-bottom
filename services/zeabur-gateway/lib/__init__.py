"""Zeabur gateway 模組化部署工具。

核心物件：
- BotConfig: 單一 WeCom bot 的設定（從 bots/<name>.yaml 讀入）
- ZeaburClient: Zeabur GraphQL API 包裝
- BotRegistry: 集中管理多個 BotConfig

未來 admin 直接 import 這些即可。
"""

from .bot_config import BotConfig, BotRegistry
from .zeabur_client import ZeaburClient, ZeaburError

__all__ = ["BotConfig", "BotRegistry", "ZeaburClient", "ZeaburError"]
