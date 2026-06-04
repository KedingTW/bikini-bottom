"""🐌 比奇堡查詢服務 — Slash Command Bot"""
import asyncio
import json
import logging
import os
import traceback
from datetime import datetime, timedelta, timezone

import discord
import docker
from discord import app_commands
from openai import AsyncOpenAI

from query_usage import (
    ACTIVITY_CATEGORIES,
    get_activity_data,
    get_tier_limit,
    get_usage_data,
)
from query_openai_usage import query_completions_usage, query_costs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ.get("DISCORD_GUILD_ID")
ALLOWED_CHANNEL_ID = os.environ.get("SLASH_BOT_CHANNEL_ID")

# Container management
ADMIN_USER_IDS = [int(uid.strip()) for uid in os.environ.get("CONCH_ADMIN_IDS", "").split(",") if uid.strip()]
OPERATOR_ROLE_IDS = [int(rid.strip()) for rid in os.environ.get("CONCH_OPERATOR_ROLE_IDS", "").split(",") if rid.strip()]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

RANK_MEDALS = {0: "🥇", 1: "🥈", 2: "🥉"}


class SlashBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            # 先同步指令到 guild
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            # 再清除全域指令殘留
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            logging.info(f"✅ 指令已同步至 guild {GUILD_ID}（全域已清除）")
        else:
            await self.tree.sync()
            logging.info("✅ 指令已全域同步")

    async def on_ready(self):
        logging.info(f"🐌 查詢服務上線！({self.user})")


bot = SlashBot()


def wrong_channel(interaction: discord.Interaction) -> bool:
    if ALLOWED_CHANNEL_ID and str(interaction.channel_id) != ALLOWED_CHANNEL_ID:
        return True
    return False


def make_progress_bar(pct: float, length: int = 10) -> str:
    filled = int(round(pct / 100 * length))
    filled = max(0, min(length, filled))
    return f"`{'█' * filled + '░' * (length - filled)}` {pct:.0f}%"


# ─── /help ───────────────────────────────────────────────

@bot.tree.command(name="help", description="列出所有可用指令")
async def help_cmd(interaction: discord.Interaction):
    if wrong_channel(interaction):
        await interaction.response.send_message("🐌 喵～請到指定頻道使用指令喔", ephemeral=True)
        return
    embed = discord.Embed(title="🐌 可用指令", color=0x00B894)
    embed.add_field(
        name="/usage [acp] [range]",
        value=(
            "額度消耗報表\n"
            "`acp`：kiro（預設）\n"
            "`range`：`1`=本月, `2`=近2月, `week:1`=近1週"
        ),
        inline=False,
    )
    embed.add_field(
        name="/activity [acp] [range]",
        value=(
            "功能使用分析\n"
            "`acp`：kiro（預設）\n"
            "`range`：`1`=本月(預設), `2`=近2月, `week:1`=近1週"
        ),
        inline=False,
    )
    embed.add_field(
        name="/openai-usage [range] [type]",
        value=(
            "OpenAI API 用量與費用\n"
            "`range`：`1`=本月(預設), `2`=近2月, `week:1`=近1週, `7d`=近7天\n"
            "`type`：`all`=全部(預設), `cost`=僅費用, `tokens`=僅token用量"
        ),
        inline=False,
    )
    embed.set_footer(text="喵～有問題請找海綿寶寶")
    await interaction.response.send_message(embed=embed)


# ─── /usage ──────────────────────────────────────────────

@bot.tree.command(name="usage", description="查詢 Kiro 使用額度")
@app_commands.describe(
    acp="ACP 名稱（預設 kiro）",
    range="時間範圍：1=本月, 2=近2月, week:1=近1週",
)
async def usage_cmd(interaction: discord.Interaction, acp: str = "kiro", range: str = None):
    if wrong_channel(interaction):
        await interaction.response.send_message("🐌 喵～請到指定頻道使用指令喔", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        if acp.lower() != "kiro":
            await interaction.followup.send(f"🐌 `{acp}` 尚未支援喵～目前只支援 kiro")
            return

        logging.info(f"/usage acp={acp} range={range}")
        data = get_usage_data(range)
        embeds = _build_usage_embeds(data)
        await interaction.followup.send(embeds=embeds[:10])
        logging.info("/usage 回覆完成")
    except Exception as e:
        logging.error(f"/usage 失敗：{e}\n{traceback.format_exc()}")
        try:
            await interaction.followup.send(f"❌ 查詢失敗：{e}")
        except Exception:
            logging.error("followup 也失敗了")


def _build_usage_embeds(data: dict) -> list[discord.Embed]:
    embeds = []
    for period in data["periods"]:
        lines = []
        users = period["users"]
        for i, u in enumerate(users):
            limit = get_tier_limit(u["tier"])
            pct = u["credits"] / limit * 100 if limit else 0
            medal = RANK_MEDALS.get(i, "　")
            bar = make_progress_bar(pct)
            lines.append(
                f"{medal} **{u['user']}**（{u['tier']}）\n"
                f"　　💰 {u['credits']:.1f} / {limit}　{bar}\n"
                f"　　💬 訊息 {u['messages']}　🗂️ 對話 {u['conversations']}"
            )
        embed = discord.Embed(
            title=f"🐌 Kiro 額度報表 — {period['label']}",
            description="\n\n".join(lines) if lines else "沒有資料喵～",
            color=0x00B894,
        )
        embed.set_footer(text="額度每月 1 日重置 | 喵～")
        embeds.append(embed)
    return embeds


# ─── /activity ───────────────────────────────────────────

@bot.tree.command(name="activity", description="分析 Kiro 的使用方式")
@app_commands.describe(
    acp="ACP 名稱（預設 kiro）",
    range="時間範圍：1=本月(預設), 2=近2月, week:1=近1週",
)
async def activity_cmd(interaction: discord.Interaction, acp: str = "kiro", range: str = None):
    if wrong_channel(interaction):
        await interaction.response.send_message("🐌 喵～請到指定頻道使用指令喔", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        if acp.lower() != "kiro":
            await interaction.followup.send(f"🐌 `{acp}` 尚未支援喵～目前只支援 kiro")
            return

        logging.info(f"/activity acp={acp} range={range}")
        data = get_activity_data(range)
        embeds = _build_activity_embeds(data)
        if embeds:
            await interaction.followup.send(embeds=embeds[:10])
        else:
            await interaction.followup.send("🐌 沒有找到任何活動資料喵～")
        logging.info("/activity 回覆完成")
    except Exception as e:
        logging.error(f"/activity 失敗：{e}\n{traceback.format_exc()}")
        try:
            await interaction.followup.send(f"❌ 查詢失敗：{e}")
        except Exception:
            logging.error("followup 也失敗了")


def _build_activity_embeds(data: dict) -> list[discord.Embed]:
    embeds = []
    for period in data["periods"]:
        lines = []
        for u in period["users"]:
            user_lines = [f"**{u['user']}**"]
            has_data = False
            for cat_name, cols in ACTIVITY_CATEGORIES.items():
                # 只顯示非零的類別
                nonzero = {c: u.get(c, 0) for c in cols if u.get(c, 0) > 0}
                if nonzero:
                    has_data = True
                    parts = "　".join(f"`{_col_label(k)}`:{v}" for k, v in nonzero.items())
                    user_lines.append(f"　　📌 {cat_name}：{parts}")
            if has_data:
                lines.append("\n".join(user_lines))
            else:
                lines.append(f"**{u['user']}**\n　　（無活動紀錄）")

        embed = discord.Embed(
            title=f"📊 Kiro 功能使用分析 — {period['label']}",
            description="\n\n".join(lines) if lines else "沒有資料喵～",
            color=0x6C5CE7,
        )
        embed.set_footer(text="喵～")
        embeds.append(embed)
    return embeds


def _col_label(col: str) -> str:
    """把欄位名轉成簡短標籤"""
    labels = {
        "chat_aicodelines": "AI程式碼行",
        "chat_messagesinteracted": "互動訊息",
        "chat_messagessent": "發送訊息",
        "inline_aicodelines": "AI程式碼行",
        "inline_acceptancecount": "採納數",
        "inline_suggestionscount": "建議數",
        "inlinechat_acceptanceeventcount": "採納次數",
        "inlinechat_acceptedlineadditions": "採納新增行",
        "inlinechat_acceptedlinedeletions": "採納刪除行",
        "inlinechat_totaleventcount": "總次數",
        "dev_acceptanceeventcount": "採納次數",
        "dev_acceptedlines": "採納行數",
        "dev_generatedlines": "生成行數",
        "dev_generationeventcount": "生成次數",
        "codefix_acceptanceeventcount": "採納次數",
        "codefix_acceptedlines": "採納行數",
        "codefix_generatedlines": "生成行數",
        "codereview_findingscount": "發現數",
        "codereview_succeededeventcount": "成功次數",
        "codereview_failedeventcount": "失敗次數",
        "testgeneration_acceptedtests": "採納測試",
        "testgeneration_generatedtests": "生成測試",
        "testgeneration_eventcount": "次數",
        "docgeneration_eventcount": "次數",
        "docgeneration_acceptedlineadditions": "採納行數",
        "transformation_eventcount": "次數",
        "transformation_linesgenerated": "生成行數",
        "transformation_linesingested": "輸入行數",
    }
    return labels.get(col, col.split("_", 1)[-1])


# ─── /openai-usage ───────────────────────────────────────

@bot.tree.command(name="openai-usage", description="查詢 OpenAI API 用量與費用")
@app_commands.describe(
    range="時間範圍：1=本月(預設), 2=近2月, week:1=近1週, 7d=近7天",
    type="查詢類型：all=全部(預設), cost=僅費用, tokens=僅token用量",
)
async def openai_usage_cmd(interaction: discord.Interaction, range: str = "1", type: str = "all"):
    if wrong_channel(interaction):
        await interaction.response.send_message("🐌 喵～請到指定頻道使用指令喔", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        logging.info(f"/openai-usage range={range} type={type}")
        embeds = []

        if type in ("all", "cost"):
            cost_data = await query_costs(range)
            embeds.append(_build_openai_cost_embed(cost_data))

        if type in ("all", "tokens"):
            token_data = await query_completions_usage(range)
            embeds.append(_build_openai_tokens_embed(token_data))

        if embeds:
            await interaction.followup.send(embeds=embeds[:10])
        else:
            await interaction.followup.send("🐌 沒有資料喵～")
        logging.info("/openai-usage 回覆完成")
    except Exception as e:
        logging.error(f"/openai-usage 失敗：{e}\n{traceback.format_exc()}")
        try:
            await interaction.followup.send(f"❌ 查詢失敗：{e}")
        except Exception:
            logging.error("followup 也失敗了")


def _build_openai_cost_embed(data: dict) -> discord.Embed:
    """費用報表 embed"""
    lines = [f"💰 **總費用：${data['total_cost']:.4f}**\n"]

    # 按 model 排序
    if data["by_model"]:
        lines.append("**依項目：**")
        for item in data["by_model"][:10]:
            if item["cost"] > 0:
                lines.append(f"　　`{item['model']}`：${item['cost']:.4f}")

    # 每日趨勢（只顯示最近幾天）
    if data["by_day"]:
        lines.append("\n**每日費用：**")
        for day in data["by_day"][-7:]:
            bar_len = min(int(day["cost"] / max(d["cost"] for d in data["by_day"]) * 8) + 1, 8) if day["cost"] > 0 else 0
            lines.append(f"　　`{day['date']}` {'█' * bar_len} ${day['cost']:.4f}")

    embed = discord.Embed(
        title=f"🐌 OpenAI 費用報表 — {data['label']}",
        description="\n".join(lines),
        color=0xFDAA4F,
    )
    embed.set_footer(text="費用為 USD | 喵～")
    return embed


def _build_openai_tokens_embed(data: dict) -> discord.Embed:
    """Token 用量 embed"""
    total_tokens = data["total_input_tokens"] + data["total_output_tokens"]
    lines = [
        f"📊 **總計：{_format_tokens(total_tokens)} tokens**",
        f"　　輸入：{_format_tokens(data['total_input_tokens'])}",
        f"　　輸出：{_format_tokens(data['total_output_tokens'])}",
        f"　　請求數：{data['total_requests']:,}\n",
    ]

    if data["by_model"]:
        lines.append("**依模型：**")
        for item in data["by_model"][:8]:
            total = item["input_tokens"] + item["output_tokens"]
            if total > 0:
                lines.append(
                    f"　　`{item['model']}`\n"
                    f"　　　　↗️ {_format_tokens(item['input_tokens'])} / "
                    f"↙️ {_format_tokens(item['output_tokens'])} / "
                    f"📨 {item['requests']:,}"
                )

    embed = discord.Embed(
        title=f"🐌 OpenAI Token 用量 — {data['label']}",
        description="\n".join(lines),
        color=0x74B9FF,
    )
    embed.set_footer(text="喵～")
    return embed


def _format_tokens(n: int) -> str:
    """數字格式化：1234567 → 1.23M, 12345 → 12.3K"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


# ─── Container Management (from magic-conch) ─────────────

ROLE_MAP = {
    "海綿寶寶": "bob", "bob": "bob",
    "派大星": "patrick", "patrick": "patrick",
    "章魚哥": "squidward", "squidward": "squidward",
    "珊迪": "sandy", "sandy": "sandy",
    "泡芙老師": "puff", "puff": "puff",
    "珍珍": "pearl", "pearl": "pearl",
    "蝦霸": "larry", "larry": "larry",
    "海螺": "conch", "conch": "conch",
    "小蝸": "gary", "gary": "gary",
    "企微": "wecom-bot", "wecom": "wecom-bot",
    "gateway": "gateway",
}

MANAGED_CONTAINERS = ["bob", "patrick", "squidward", "sandy", "puff", "pearl", "larry", "conch", "gary"]


def get_docker_client() -> docker.DockerClient:
    docker_host = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    return docker.DockerClient(base_url=docker_host)


def resolve_container_name(name: str) -> str | None:
    return ROLE_MAP.get(name.lower().strip())


def is_admin(interaction: discord.Interaction) -> bool:
    return interaction.user.id in ADMIN_USER_IDS


def is_operator(interaction: discord.Interaction) -> bool:
    if is_admin(interaction):
        return True
    if hasattr(interaction.user, "roles"):
        user_role_ids = [r.id for r in interaction.user.roles]
        return any(rid in user_role_ids for rid in OPERATOR_ROLE_IDS)
    return False


def _display_name(container_name: str) -> str:
    names = {
        "bob": "海綿寶寶", "patrick": "派大星", "squidward": "章魚哥",
        "sandy": "珊迪", "puff": "泡芙老師", "pearl": "珍珍",
        "larry": "蝦霸", "conch": "神奇海螺",
        "slash-bot": "小蝸", "gary": "小蝸", "wecom-bot": "企微Bot", "gateway": "Gateway",
    }
    return names.get(container_name, container_name)


def _status_emoji(status: str) -> str:
    return {"running": "🟢", "exited": "🔴", "restarting": "🟡", "paused": "⏸️", "dead": "💀"}.get(status, "❓")


def _format_uptime(started_at: str) -> str:
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - started
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return "?"


def _get_status_line(name: str, client: docker.DockerClient) -> str:
    try:
        c = client.containers.get(name)
        emoji = _status_emoji(c.status)
        started_at = c.attrs["State"].get("StartedAt", "")
        uptime = _format_uptime(started_at)
        base = f"{emoji} **{_display_name(name)}**"
        if c.status != "running":
            return f"{base} — {c.status}"
        return f"{base} — running (uptime {uptime})"
    except docker.errors.NotFound:
        return f"❓ **{_display_name(name)}** — 不存在"


@bot.tree.command(name="status", description="🐌 查看容器狀態")
@app_commands.describe(target="角色名稱，不填則查看全部")
async def status_cmd(interaction: discord.Interaction, target: str = ""):
    await interaction.response.defer()
    try:
        client = get_docker_client()
        if not target:
            lines = [_get_status_line(name, client) for name in MANAGED_CONTAINERS]
            client.close()
            await interaction.followup.send(f"🐌 全員回報喵～\n\n" + "\n".join(lines))
        else:
            container_name = resolve_container_name(target)
            if not container_name:
                client.close()
                await interaction.followup.send(f"🐌 不認識「{target}」喵～")
                return
            line = _get_status_line(container_name, client)
            client.close()
            await interaction.followup.send(f"🐌 {line}")
    except Exception as e:
        logging.error(f"/status 失敗：{e}\n{traceback.format_exc()}")
        await interaction.followup.send(f"🐌 出了點問題喵～ `{e}`")


@bot.tree.command(name="heal", description="🐌 重啟容器")
@app_commands.describe(target="角色名稱")
async def heal_cmd(interaction: discord.Interaction, target: str):
    if not is_operator(interaction):
        await interaction.response.send_message("🐌 不允許喵～", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        container_name = resolve_container_name(target)
        if not container_name:
            await interaction.followup.send(f"🐌 不認識「{target}」喵～")
            return
        client = get_docker_client()
        container = client.containers.get(container_name)
        container.restart(timeout=10)
        client.close()
        await interaction.followup.send(f"🐌 {_display_name(container_name)}已重啟喵～")
    except docker.errors.NotFound:
        await interaction.followup.send(f"🐌 {target}不存在喵～")
    except Exception as e:
        logging.error(f"/heal 失敗：{e}\n{traceback.format_exc()}")
        await interaction.followup.send(f"🐌 治療失敗喵～ `{e}`")


@bot.tree.command(name="logs", description="🐌 查看容器近期 log")
@app_commands.describe(target="角色名稱", lines="行數（預設 20，上限 50）")
async def logs_cmd(interaction: discord.Interaction, target: str, lines: int = 20):
    await interaction.response.defer()
    try:
        container_name = resolve_container_name(target)
        if not container_name:
            await interaction.followup.send(f"🐌 不認識「{target}」喵～")
            return
        client = get_docker_client()
        lines = min(lines, 50)
        c = client.containers.get(container_name)
        log_output = c.logs(tail=lines, timestamps=False).decode("utf-8", errors="replace")
        if len(log_output) > 1900:
            log_output = log_output[-1900:]
        client.close()
        await interaction.followup.send(
            f"🐌 **{_display_name(container_name)}** 最近 {lines} 行 log：\n```\n{log_output}\n```"
        )
    except docker.errors.NotFound:
        await interaction.followup.send(f"🐌 {target}不存在喵～")
    except Exception as e:
        logging.error(f"/logs 失敗：{e}\n{traceback.format_exc()}")
        await interaction.followup.send(f"🐌 讀取失敗喵～ `{e}`")


@bot.tree.command(name="archive", description="🐌 封存當前 thread，開新 thread 延續對話")
@app_commands.describe(reason="封存原因（選填）")
async def archive_cmd(interaction: discord.Interaction, reason: str = "對話過長"):
    channel = interaction.channel
    if not isinstance(channel, discord.Thread):
        await interaction.response.send_message("🐌 這個指令只能在 thread 裡使用喵～", ephemeral=True)
        return
    if not is_operator(interaction):
        await interaction.response.send_message("🐌 不允許喵～", ephemeral=True)
        return
    await interaction.response.defer()
    try:
        thread = channel
        parent_channel = thread.parent
        messages = []
        async for msg in thread.history(limit=300, oldest_first=True):
            messages.append(msg)
        msg_count = len(messages)
        if msg_count < 5:
            await interaction.followup.send("🐌 訊息太少，不需要封存喵～")
            return

        # Generate summary
        summary = await _summarize_messages(messages)

        # Find bot participants
        bot_ids = set()
        for msg in messages:
            if msg.author.bot and msg.author.id != bot.user.id:
                bot_ids.add(msg.author.id)
        mentions_str = " ".join(f"<@{uid}>" for uid in bot_ids)

        new_thread_title = f"{thread.name}（續）" if len(thread.name) < 90 else thread.name[:87] + "…（續）"

        await thread.send(
            f"📦 **此對話已封存**（{reason}，共 {msg_count} 則訊息）\n"
            f"由 {interaction.user.mention} 執行封存。\n"
            f"討論將延續至新 thread。"
        )

        opener_content = (
            f"🔄 **延續討論**（封存自：{thread.name}）\n\n"
            f"{mentions_str}\n\n"
            f"**前情提要：**\n{summary}"
        )
        if len(opener_content) > 1900:
            opener_content = opener_content[:1900] + "\n\n（摘要已截斷）"

        new_msg = await parent_channel.send(opener_content)
        new_thread = await new_msg.create_thread(name=new_thread_title)

        await new_thread.send(
            f"🐌 此 thread 延續自封存的對話喵～\n"
            f"原 thread：https://discord.com/channels/{interaction.guild_id}/{thread.id}\n"
            f"封存原因：{reason}\n"
            f"原訊息數：{msg_count}"
        )

        await interaction.followup.send(
            f"🐌 封存完畢喵～\n"
            f"📦 原 thread：{msg_count} 則訊息已封存\n"
            f"🆕 新 thread：{new_thread.mention}\n"
            f"👥 已 mention {len(bot_ids)} 個 bot 參與者"
        )
    except Exception as e:
        logging.error(f"/archive 失敗：{e}\n{traceback.format_exc()}")
        await interaction.followup.send(f"🐌 封存失敗喵～ `{e}`")


async def _summarize_messages(messages: list[discord.Message]) -> str:
    if not openai_client:
        recent = messages[-20:]
        lines = [f"{m.author.display_name}: {m.content[:100]}" for m in recent if m.content]
        return "（無法產生 AI 摘要，以下為最近對話）\n" + "\n".join(lines)

    recent = messages[-100:]
    conversation = "\n".join(
        f"[{m.created_at.strftime('%m/%d %H:%M')}] {m.author.display_name}: {m.content[:200]}"
        for m in recent if m.content
    )
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "你是一個對話摘要助手。請用繁體中文總結以下 Discord 對話，包含：\n"
                    "1. 討論主題\n2. 目前進度/結論\n3. 待辦事項或未解決的問題\n"
                    "4. 參與者各自的立場/貢獻\n保持簡潔，不超過 500 字。"
                )},
                {"role": "user", "content": conversation},
            ],
            max_tokens=800,
            temperature=0.3,
        )
        return response.choices[0].message.content or "（摘要產生失敗）"
    except Exception as e:
        logging.error(f"OpenAI 摘要失敗：{e}")
        recent = messages[-10:]
        lines = [f"{m.author.display_name}: {m.content[:80]}" for m in recent if m.content]
        return f"（AI 摘要失敗：{e}）\n最近對話：\n" + "\n".join(lines)


if __name__ == "__main__":
    bot.run(TOKEN)
