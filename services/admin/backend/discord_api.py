"""Discord REST API wrapper using Karen bot token."""
import os
import httpx

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
BASE = "https://discord.com/api/v10"

# 本地暱稱對照表（Discord user ID → 中文名）
NICK_MAP = {
    "565206708473823233": "蔡旻哲",
    "1465924775204487263": "林潔庭",
    "1494150209637318866": "吳珈瑄",
    "1505819268384817313": "楊詠仁",
    "1505875884807164085": "小美女",
    "1506898528344080478": "Grace Chen",
    "1506991004815855656": "馥寧",
    "1511580116352897094": "Jackson",
}


def _headers():
    return {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}


async def list_members(limit=100, after=None):
    """List guild members."""
    params = {"limit": min(limit, 1000)}
    if after:
        params["after"] = after
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{GUILD_ID}/members", headers=_headers(), params=params)
        r.raise_for_status()
        members = r.json()
    return [
        {
            "id": m["user"]["id"],
            "username": m["user"]["username"],
            "display_name": NICK_MAP.get(m["user"]["id"]) or m["user"].get("global_name") or m.get("nick") or m["user"]["username"],
            "nick": NICK_MAP.get(m["user"]["id"]) or m.get("nick"),
            "avatar": m["user"].get("avatar"),
            "roles": m.get("roles", []),
            "joined_at": m.get("joined_at"),
        }
        for m in members
    ]


async def list_roles():
    """List guild roles, excluding bot-specific and @everyone."""
    # Bot 角色名稱（需要過濾的）
    BOT_ROLE_NAMES = {"海綿寶寶", "派大星", "泡芙老師", "章魚哥", "珊迪", "神奇海螺", "小蝸", "珍珍", "蝦霸", "凱倫", "海超人"}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{GUILD_ID}/roles", headers=_headers())
        r.raise_for_status()
        roles = r.json()
    return sorted(
        [{"id": r["id"], "name": r["name"], "color": r["color"], "position": r["position"]}
         for r in roles
         if not r.get("managed", False) and r["name"] != "@everyone" and r["name"] not in BOT_ROLE_NAMES],
        key=lambda x: x["position"],
        reverse=True,
    )


async def add_role(user_id: str, role_id: str):
    """Add role to member."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(f"{BASE}/guilds/{GUILD_ID}/members/{user_id}/roles/{role_id}", headers=_headers())
        r.raise_for_status()


async def remove_role(user_id: str, role_id: str):
    """Remove role from member."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(f"{BASE}/guilds/{GUILD_ID}/members/{user_id}/roles/{role_id}", headers=_headers())
        r.raise_for_status()


async def list_channels():
    """List guild text channels."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{GUILD_ID}/channels", headers=_headers())
        r.raise_for_status()
        channels = r.json()
    # Only text channels (0) and announcements (5)
    return [
        {"id": c["id"], "name": c["name"], "type": c["type"], "parent_id": c.get("parent_id")}
        for c in channels if c["type"] in (0, 5, 15)
    ]


async def send_message(channel_id: str, content: str):
    """Send a message to a channel."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/channels/{channel_id}/messages",
            headers=_headers(),
            json={"content": content},
        )
        r.raise_for_status()
        return r.json()


async def set_nickname(user_id: str, nick: str):
    """Set member nickname in guild."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{BASE}/guilds/{GUILD_ID}/members/{user_id}",
            headers=_headers(),
            json={"nick": nick},
        )
        r.raise_for_status()
