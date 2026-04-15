"""🐌 比奇堡查詢服務 — Slash Command Bot"""
import os
from collections import defaultdict

import discord
from discord import app_commands

from query_usage import read_cache, run_athena_query, write_cache

TOKEN = os.environ["DISCORD_BOT_TOKEN"]


class SlashBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ 指令已同步")

    async def on_ready(self):
        print(f"🐌 查詢服務上線！({self.user})")


bot = SlashBot()


# ─── /help ───────────────────────────────────────────────
@bot.tree.command(name="help", description="列出所有可用指令")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🐌 可用指令", color=0x00B894)
    embed.add_field(
        name="/help",
        value="列出所有可用指令",
        inline=False,
    )
    embed.add_field(
        name="/usage [mode]",
        value="查詢 Kiro 使用量（近 30 天）\n`summary`：加總摘要（預設）\n`full`：每日明細",
        inline=False,
    )
    embed.set_footer(text="喵～有問題請找海綿寶寶")
    await interaction.response.send_message(embed=embed)


# ─── /usage ──────────────────────────────────────────────
def get_usage_data():
    data = read_cache()
    if not data:
        data = run_athena_query()
        write_cache(data)
    return data


def build_summary_embed(data):
    by_user = defaultdict(lambda: {"credits": 0.0, "messages": 0, "conversations": 0, "tier": ""})
    for r in data:
        u = by_user[r["user"]]
        u["credits"] += r["credits_used"]
        u["messages"] += r["total_messages"]
        u["conversations"] += r["chat_conversations"]
        u["tier"] = r["tier"] or u["tier"]

    embed = discord.Embed(title="🐌 Kiro 使用量報表（近 30 天）", color=0x00B894)
    for user, s in sorted(by_user.items()):
        embed.add_field(
            name=f"{user}（{s['tier']}）",
            value=f"💰 額度：{s['credits']:.1f}\n💬 訊息：{s['messages']}\n🗂️ 對話：{s['conversations']}",
            inline=True,
        )
    embed.set_footer(text=f"共 {len(data)} 筆原始資料 | 喵～")
    return embed


def build_full_embeds(data):
    """每日明細，分多個 embed 避免超過字數限制"""
    by_date = defaultdict(list)
    for r in data:
        by_date[r["date"]].append(r)

    embeds = []
    lines = []
    for date in sorted(by_date.keys(), reverse=True):
        for r in by_date[date]:
            lines.append(
                f"`{date}` **{r['user']}** — "
                f"💰{r['credits_used']:.1f} 💬{r['total_messages']} 🗂️{r['chat_conversations']}"
            )

    chunk, length = [], 0
    for line in lines:
        if length + len(line) + 1 > 3900:
            embeds.append(discord.Embed(description="\n".join(chunk), color=0x00B894))
            chunk, length = [], 0
        chunk.append(line)
        length += len(line) + 1
    if chunk:
        embeds.append(discord.Embed(description="\n".join(chunk), color=0x00B894))

    if embeds:
        embeds[0].title = "🐌 Kiro 使用量明細（近 30 天）"
        embeds[-1].set_footer(text=f"共 {len(data)} 筆資料 | 喵～")
    return embeds


@bot.tree.command(name="usage", description="查詢 Kiro 使用量（近 30 天）")
@app_commands.describe(mode="顯示模式：summary（加總摘要）或 full（每日明細）")
@app_commands.choices(mode=[
    app_commands.Choice(name="summary", value="summary"),
    app_commands.Choice(name="full", value="full"),
])
async def usage(interaction: discord.Interaction, mode: app_commands.Choice[str] = None):
    await interaction.response.defer()
    try:
        data = get_usage_data()
        mode_val = mode.value if mode else "summary"
        if mode_val == "full":
            embeds = build_full_embeds(data)
            await interaction.followup.send(embeds=embeds[:10])
        else:
            embed = build_summary_embed(data)
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ 查詢失敗：{e}")


if __name__ == "__main__":
    bot.run(TOKEN)
