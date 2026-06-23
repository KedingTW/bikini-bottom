"""Discord REST API wrapper using admin bot token."""
import os
import httpx

BOT_TOKEN = os.environ.get("DISCORD_ADMIN_BOT_TOKEN", os.environ.get("DISCORD_BOT_TOKEN", ""))
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
    return {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json", "User-Agent": "DiscordBot (https://bikini-bottom.dev, 1.0)"}


async def list_members(limit=100, after=None, guild_id=None):
    """List guild members."""
    gid = guild_id or GUILD_ID
    BOT_ROLE_NAMES = {"海綿寶寶", "派大星", "泡芙老師", "章魚哥", "珊迪", "神奇海螺", "小蝸", "珍珍", "蝦霸", "凱倫", "海超人"}

    params = {"limit": min(limit, 1000)}
    if after:
        params["after"] = after
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{gid}/members", headers=_headers(), params=params)
        r.raise_for_status()
        members = r.json()
        r2 = await client.get(f"{BASE}/guilds/{gid}/roles", headers=_headers())
        r2.raise_for_status()
        all_roles = r2.json()

    bot_role_ids = {r["id"] for r in all_roles if r["name"] in BOT_ROLE_NAMES or r.get("managed", False)}

    return [
        {
            "id": m["user"]["id"],
            "username": m["user"]["username"],
            "name": NICK_MAP.get(m["user"]["id"]) or m["user"].get("global_name") or m.get("nick") or m["user"]["username"],
            "display_name": NICK_MAP.get(m["user"]["id"]) or m["user"].get("global_name") or m.get("nick") or m["user"]["username"],
            "nick": NICK_MAP.get(m["user"]["id"]) or m.get("nick"),
            "bot": m["user"].get("bot", False),
            "avatar": m["user"].get("avatar"),
            "roles": [rid for rid in m.get("roles", []) if rid not in bot_role_ids],
            "joined_at": m.get("joined_at"),
        }
        for m in members
    ]


async def list_roles(guild_id=None):
    """List guild roles, excluding bot-specific and @everyone."""
    gid = guild_id or GUILD_ID
    BOT_ROLE_NAMES = {"海綿寶寶", "派大星", "泡芙老師", "章魚哥", "珊迪", "神奇海螺", "小蝸", "珍珍", "蝦霸", "凱倫", "海超人"}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{gid}/roles", headers=_headers())
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


async def list_channels(guild_id=None):
    """List guild text channels."""
    gid = guild_id or GUILD_ID
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{gid}/channels", headers=_headers())
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


async def list_active_threads(guild_id=None):
    """List all active threads in guild."""
    gid = guild_id or GUILD_ID
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/guilds/{gid}/threads/active", headers=_headers())
        r.raise_for_status()
        data = r.json()
    threads = data.get("threads", [])
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "parent_id": t.get("parent_id"),
            "archived": t.get("thread_metadata", {}).get("archived", False),
            "locked": t.get("thread_metadata", {}).get("locked", False),
            "message_count": t.get("message_count", 0),
            "created_at": t.get("thread_metadata", {}).get("create_timestamp"),
            "last_activity": _snowflake_to_iso(t.get("last_message_id")),
            "owner_id": t.get("owner_id"),
            "applied_tags": t.get("applied_tags", []),
        }
        for t in threads
    ]


def _snowflake_to_iso(snowflake_id):
    """Convert Discord snowflake ID to ISO timestamp."""
    if not snowflake_id:
        return None
    try:
        ts_ms = (int(snowflake_id) >> 22) + 1420070400000
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return None


async def list_forum_tags(channel_id: str):
    """Get available tags for a forum channel."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{BASE}/channels/{channel_id}", headers=_headers())
        r.raise_for_status()
        ch = r.json()
    return ch.get("available_tags", [])


async def archive_thread(thread_id: str):
    """Archive a thread."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{BASE}/channels/{thread_id}",
            headers=_headers(),
            json={"archived": True},
        )
        r.raise_for_status()


async def update_thread_tags(thread_id: str, tag_ids: list):
    """Update applied tags on a forum thread."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.patch(
            f"{BASE}/channels/{thread_id}",
            headers=_headers(),
            json={"applied_tags": tag_ids},
        )
        r.raise_for_status()


async def get_channel_messages(channel_id: str, limit: int = 100, before: str = None):
    """Get recent messages from a channel."""
    params = {"limit": min(limit, 100)}
    if before:
        params["before"] = before
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{BASE}/channels/{channel_id}/messages",
            headers=_headers(),
            params=params,
        )
        r.raise_for_status()
        return r.json()
