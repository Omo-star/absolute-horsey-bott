import asyncio
import datetime
import json

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

STATUS_URL = "https://raw.githubusercontent.com/Omo-star/icbmsaregoated2/main/lichess_status.json"

_cached_data = None
_cached_etag = None


async def fetch_status():
    global _cached_data, _cached_etag
    headers = {}
    if _cached_etag is not None:
        headers["If-None-Match"] = _cached_etag
    async with aiohttp.ClientSession() as session:
        async with session.get(STATUS_URL, headers=headers) as resp:
            if resp.status == 304 and _cached_data is not None:
                return _cached_data
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            text = await resp.text()
            data = json.loads(text)
            _cached_data = data
            _cached_etag = resp.headers.get("ETag")
            return data


def fmt_time(seconds):
    try:
        seconds = int(seconds)
        return f"{seconds//60}:{seconds%60:02d}"
    except:
        return "N/A"


def fmt_moves(moves_str):
    if not moves_str:
        return "No moves found."
    moves = moves_str.split()
    out = []
    n = 1
    for i in range(0, len(moves), 2):
        w = moves[i]
        b = moves[i + 1] if i + 1 < len(moves) else "…"
        out.append(f"**{n}.** {w}   {b}")
        n += 1
    return "\n".join(out)


def paginate_moves(moves_str, limit=900):
    full = fmt_moves(moves_str)
    if len(full) <= limit:
        return [full]
    lines = full.split("\n")
    pages = []
    buf = []
    length = 0
    for line in lines:
        if length + len(line) + 1 > limit and buf:
            pages.append("\n".join(buf))
            buf = [line]
            length = len(line) + 1
        else:
            buf.append(line)
            length += len(line) + 1
    if buf:
        pages.append("\n".join(buf))
    return pages


def make_status_embed(data: dict) -> discord.Embed:
    online = data.get("online", False)
    playing = data.get("playing", False)
    rating = data.get("rating", "N/A")
    opponent = data.get("opponent", "None")
    variant = data.get("variant", "N/A")
    time_control = data.get("time_control", "N/A")
    time_left = data.get("time_left", "N/A")
    timestamp = data.get("timestamp", None)
    last_game = data.get("last_game", {})

    try:
        ts = datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Unknown"
    except:
        ts = "Unknown"

    e = discord.Embed(
        title="🤖 Lichess Bot Status",
        description="Live overview for my Lichess bot",
        color=discord.Color.dark_purple()
    )
    e.add_field(name="Status", value=f"🟢 Online: `{online}`\n🎮 Playing: `{playing}`", inline=False)
    e.add_field(name="Rating", value=f"📈 `{rating}`", inline=True)
    e.add_field(name="Opponent", value=f"⚔️ `{opponent}`", inline=True)
    e.add_field(name="Variant", value=f"♜ `{variant}`", inline=True)
    e.add_field(name="Time Control", value=f"⏱️ `{time_control}`", inline=True)
    e.add_field(name="Time Left", value=f"⌛ `{time_left}`", inline=True)

    if last_game:
        result = last_game.get("result", "Unknown")
        opp = last_game.get("opponent", "Unknown")
        rdelta = last_game.get("rating_delta", 0)
        e.add_field(
            name="Last Game",
            value=f"**Result:** `{result}`\n**Opponent:** `{opp}`\n**Rating Δ:** `{rdelta:+}`\nUse `/lichess_game` to view full game.",
            inline=False
        )

    e.set_footer(text=f"Updated: {ts}")
    return e


def make_game_embed(game: dict, moves_page: str, page_index: int, page_total: int) -> discord.Embed:
    opponent = game.get("opponent", "Unknown")
    result = game.get("result", "Unknown")
    duration = game.get("duration", "N/A")
    bot_color = game.get("bot_color", "Unknown")
    termination = game.get("termination", "Unknown")
    rating_before = game.get("rating_before", "N/A")
    rating_after = game.get("rating_after", "N/A")

    e = discord.Embed(
        title="📜 Full Game Viewer",
        description=f"Opponent: **{opponent}**\nResult: **{result}**",
        color=discord.Color.dark_purple()
    )
    e.add_field(name="Bot Color", value=f"🎨 `{bot_color}`", inline=True)
    e.add_field(name="Duration", value=f"⏱️ `{fmt_time(duration)}`", inline=True)
    e.add_field(name="Termination", value=f"💀 `{termination}`", inline=True)
    e.add_field(
        name="Rating Change",
        value=f"Before: `{rating_before}` → After: `{rating_after}`",
        inline=False
    )
    e.add_field(
        name=f"Moves (Page {page_index+1}/{page_total})",
        value=f"```\n{moves_page}\n```",
        inline=False
    )
    return e


class GameView(discord.ui.View):
    def __init__(self, game: dict, pages: list[str]):
        super().__init__(timeout=180)
        self.game = game
        self.pages = pages
        self.index = 0

    async def update_message(self, interaction: discord.Interaction):
        embed = make_game_embed(self.game, self.pages[self.index], self.index, len(self.pages))
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self.update_message(interaction)


class StreamView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)
        self.stopped = False

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stopped = True
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.response.edit_message(view=self)


class LichessCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lichess", description="Show the current Lichess bot status dashboard.")
    async def lichess(self, interaction: discord.Interaction):
        try:
            data = await fetch_status()
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Failed to fetch Lichess status:\n```{e}```",
                ephemeral=True
            )
        embed = make_status_embed(data)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="lichess_game", description="View the full move list of the bot’s latest Lichess game.")
    async def lichess_game(self, interaction: discord.Interaction):
        try:
            data = await fetch_status()
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Failed to fetch Lichess data:\n```{e}```",
                ephemeral=True
            )
        game = data.get("last_game", None)
        if not game:
            return await interaction.response.send_message(
                "⚠️ No last game found in data.",
                ephemeral=True
            )
        moves = game.get("moves", "")
        pages = paginate_moves(moves)
        view = GameView(game, pages)
        embed = make_game_embed(game, pages[0], 0, len(pages))
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="lichess_stream", description="Live-updating Lichess bot status panel.")
    async def lichess_stream(self, interaction: discord.Interaction):
        try:
            data = await fetch_status()
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Failed to fetch Lichess status:\n```{e}```",
                ephemeral=True
            )
        view = StreamView()
        embed = make_status_embed(data)
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        for _ in range(120):
            await asyncio.sleep(10)
            if view.stopped:
                break
            try:
                data = await fetch_status()
            except:
                continue
            embed = make_status_embed(data)
            try:
                await message.edit(embed=embed, view=view)
            except:
                break

async def setup(bot):
    await bot.add_cog(LichessCog(bot))
