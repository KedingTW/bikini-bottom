"""
BotConfig：讀取 bots/<name>.yaml 的設定。

使用方式：
    registry = BotRegistry.load("services/zeabur-gateway/bots")
    for bot in registry.enabled():
        print(bot.name, bot.domain, bot.env_var_names())

未來 admin web UI 也會用這支模組顯示 bot 列表、新增/編輯 bot。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required. Install: pip install --user pyyaml"
    ) from exc


@dataclass(frozen=True)
class BotConfig:
    """單一 WeCom bot 的設定。對應一個 Zeabur gateway service。"""

    name: str
    display_name: str
    description: str
    domain: str
    agent: str
    env_var_prefix: str
    wecom_secret_keys: tuple[str, ...]
    pool_max_sessions: int = 10
    enabled: bool = False
    source_path: Path | None = field(default=None, compare=False)

    # ─── Derived properties ──────────────────────────────────
    @property
    def zeabur_service_name(self) -> str:
        """Zeabur 上的 service 命名規則：gateway-<bot-name>。"""
        return f"gateway-{self.name}"

    @property
    def webhook_url(self) -> str:
        """WeCom 後台填入的 callback URL。"""
        return f"https://{self.domain}/webhook/wecom"

    @property
    def ws_url(self) -> str:
        """地端 wecom-bot agent 連線用的 wss URL。"""
        return f"wss://{self.domain}/ws"

    def env_var_names(self) -> dict[str, str]:
        """
        WeCom 5 個密鑰在 .env 的變數名映射。
        key   = gateway 內讀的環境變數名（image 預期的名字）
        value = 部署時從 .env 讀的變數名
        """
        return {
            key: f"{self.env_var_prefix}_{key}"
            for key in self.wecom_secret_keys
        }

    def env_vars_from_environ(self) -> dict[str, str]:
        """從 os.environ 讀出對應 .env 的值。缺值會 raise。"""
        result: dict[str, str] = {}
        missing: list[str] = []
        for gateway_name, env_name in self.env_var_names().items():
            value = os.environ.get(env_name)
            if value is None or value == "":
                missing.append(env_name)
            else:
                result[gateway_name] = value
        if missing:
            raise KeyError(
                f"Missing env vars for bot '{self.name}': {', '.join(missing)}"
            )
        return result

    # ─── Loaders ─────────────────────────────────────────────
    @classmethod
    def from_yaml(cls, path: Path) -> "BotConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            name=data["name"],
            display_name=data.get("displayName", data["name"]),
            description=data.get("description", ""),
            domain=data["domain"],
            agent=data["agent"],
            env_var_prefix=data["envVarPrefix"],
            wecom_secret_keys=tuple(data.get("wecom", {}).get("secretKeys", [])),
            pool_max_sessions=int(data.get("pool", {}).get("maxSessions", 10)),
            enabled=bool(data.get("enabled", False)),
            source_path=path,
        )


@dataclass
class BotRegistry:
    """集中管理多個 BotConfig，從 bots/ 目錄讀入。"""

    bots: list[BotConfig] = field(default_factory=list)

    @classmethod
    def load(cls, bots_dir: str | Path) -> "BotRegistry":
        bots_path = Path(bots_dir)
        if not bots_path.exists():
            raise FileNotFoundError(f"bots dir not found: {bots_path}")
        bots: list[BotConfig] = []
        for entry in sorted(bots_path.glob("*.yaml")):
            if entry.name.startswith("_"):
                continue  # skip _template.yaml
            bots.append(BotConfig.from_yaml(entry))
        return cls(bots=bots)

    def enabled(self) -> Iterator[BotConfig]:
        return (b for b in self.bots if b.enabled)

    def by_name(self, name: str) -> BotConfig:
        for b in self.bots:
            if b.name == name:
                return b
        raise KeyError(f"bot not found: {name}")
