import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

STATUS_FILE = "lichess_data/lichess_status.json"


def fmt_time(seconds):
    try:
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"
    except:
        return "N/A"


def fmt_moves(moves_str):
    if not moves_str:
        return "No moves found."

    moves = moves_str.split()
    result = []
    move_num = 1

    for i in range(0, len(moves), 2):
        white = moves[i]
        black = moves[i+1] if i+1 < len(moves) else "…"
        result.append(f"**{move_num}.** {white}   {black}")
        move_num += 1

    return "\n".join(result)


class LichessCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="lichess",
        description="Show the current Lichess bot status dashboard."
    )
    async def lichess(self, interaction: discord.Interaction):

        if not os.path.exists(STATUS_FILE):
            return await interaction.response.send_message(
                "⚠️ No Lichess status file found.",
                ephemeral=True
            )

        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Error loading status file:\n```{e}```",
                ephemeral=True
            )

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
            if timestamp:
                dt = datetime.datetime.fromisoformat(timestamp)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = "Unknown"
        except:
            ts = "Unknown"

        e = discord.Embed(
            title="🤖 Lichess Bot Status",
            description="Live overview for my Lichess bot",
            color=discord.Color.dark_purple()
        )

        e.add_field(
            name="Status",
            value=f"🟢 Online: `{online}`\n🎮 Playing: `{playing}`",
            inline=False
        )

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
                value=(
                    f"**Result:** `{result}`\n"
                    f"**Opponent:** `{opp}`\n"
                    f"**Rating Δ:** `{rdelta:+}`\n"
                    f"Use `/lichess_game` to view full game."
                ),
                inline=False
            )

        e.set_footer(text=f"Updated: {ts}")
        await interaction.response.send_message(embed=e)
    @app_commands.command(
        name="lichess_game",
        description="View the full move list and details of the bot’s latest Lichess game."
    )
    async def lichess_game(self, interaction: discord.Interaction):

        if not os.path.exists(STATUS_FILE):
            return await interaction.response.send_message(
                "⚠️ No Lichess data found.",
                ephemeral=True
            )

        try:
            with open(STATUS_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            return await interaction.response.send_message(
                f"❌ Could not load file:\n```{e}```",
                ephemeral=True
            )

        game = data.get("last_game", None)
        if not game:
            return await interaction.response.send_message(
                "⚠️ No last game found in data.",
                ephemeral=True
            )

        opponent = game.get("opponent", "Unknown")
        result = game.get("result", "Unknown")
        moves = game.get("moves", "")
        duration = game.get("duration", "N/A")
        bot_color = game.get("bot_color", "Unknown")
        termination = game.get("termination", "Unknown")
        rating_before = game.get("rating_before", "N/A")
        rating_after = game.get("rating_after", "N/A")

        pretty_moves = fmt_moves(moves)

        e = discord.Embed(
            title=f"📜 Full Game Viewer",
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
            name="Moves",
            value=f"```\n{pretty_moves}\n```",
            inline=False
        )

        await interaction.response.send_message(embed=e)


async def setup(bot):
    await bot.add_cog(LichessCog(bot))
