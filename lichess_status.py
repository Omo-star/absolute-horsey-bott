import discord, json, os, aiohttp, asyncio
from discord.ext import commands
from discord import app_commands

GITHUB_PAT = os.getenv("PAT")

class LichessStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lichess", description="Show Lichess bot status.")
    async def lichess(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        async with aiohttp.ClientSession() as session:
            await session.post(
                "https://api.github.com/repos/Omo-star/icbmsaregoated2/dispatches",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {GITHUB_PAT}",
                },
                json={"event_type": "download-lichess-status"}
            )

        await asyncio.sleep(2)

        if not os.path.exists("lichess_status.json"):
            await interaction.followup.send("No status available.")
            return

        data = json.load(open("lichess_status.json"))

        embed = discord.Embed(
            title="Lichess Bot Status",
            color=discord.Color.blurple(),
        )

        if data.get("finished"):
            embed.description = (
                f"Game Finished\n"
                f"Winner: {data['winner']}\n"
                f"Streak: {data['streak']}"
            )
        else:
            embed.add_field(name="Game ID", value=data["game_id"])
            embed.add_field(name="Opponent", value=data["opponent"])
            embed.add_field(name="Turn", value=data["turn"])
            embed.add_field(name="Eval", value=data["last_eval"], inline=False)
            embed.add_field(name="White Time", value=f"{data['white_time']:.1f}s")
            embed.add_field(name="Black Time", value=f"{data['black_time']:.1f}s")

            if "ratings" in data:
                r = data["ratings"]
                embed.add_field(
                    name="Ratings",
                    value=f"Blitz: {r['blitz']}\nRapid: {r['rapid']}\nBullet: {r['bullet']}",
                    inline=False,
                )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LichessStatus(bot))
