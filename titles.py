import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user
from economy_shared import save_state

try:
    from achievement import get_profile_meta
except Exception:
    get_profile_meta = None


def normalize(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def unlocked_titles(uid: int):
    data = get_user(uid)
    titles = ["fresh spawn"]

    if get_profile_meta:
        meta = get_profile_meta(uid, data)
        title = meta.get("title")
        if title:
            titles.append(title)
        unlocked_ids = {a["id"] for a in meta.get("results", []) if a.get("unlocked")}
        mapping = {
            "starter_wallet": "coin flipper",
            "five_figures": "stable banker",
            "capital_engine": "market titan",
            "pack_starter": "rookie tamer",
            "creature_curator": "beast collector",
            "menagerie_lord": "menagerie lord",
            "full_squad": "squad captain",
            "alpha_pack": "pack alpha",
            "rare_bloodline": "rare bloodline",
            "deep_delver": "deep delver",
            "worldbreaker": "worldbreaker",
            "crown_duelist": "crown duelist",
            "abyss_walker": "abyss walker",
            "fracture_scholar": "fracture scholar",
            "ghost_operator": "ghost operator",
            "all_terrain": "all-terrain user",
            "all_rounder": "all-rounder",
            "horselord_prime": "horselord prime",
        }
        for achievement_id, title_name in mapping.items():
            if achievement_id in unlocked_ids:
                titles.append(title_name)
    else:
        balance = int(data.get("balance", 0) or 0)
        if balance >= 10000:
            titles.append("stable banker")

    seen = set()
    out = []
    for item in titles:
        key = normalize(item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


class Titles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="titles", description="View your unlocked titles.")
    async def titles(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        data = get_user(target.id)
        titles = unlocked_titles(target.id)
        equipped = data.get("equipped_title") or titles[0]

        embed = discord.Embed(
            title=f"🎖️ {target.display_name}'s Titles",
            description=f"equipped: `{equipped}`\nunlocked: `{len(titles)}`",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Unlocked", value="\n".join(f"• {title}" for title in titles[:25]), inline=False)
        embed.set_footer(text="use /title_equip <title> to equip one")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="title_equip", description="Equip one of your unlocked titles.")
    async def title_equip(self, interaction: discord.Interaction, title: str):
        data = get_user(interaction.user.id)
        titles = unlocked_titles(interaction.user.id)
        wanted = normalize(title)
        match = next((t for t in titles if normalize(t) == wanted), None)
        if not match:
            await interaction.response.send_message("that title isnt unlocked for you", ephemeral=True)
            return
        data["equipped_title"] = match
        save_state()
        await interaction.response.send_message(f"equipped title set to `{match}`")


async def setup(bot):
    print("Loading Titles Cog...")
    await bot.add_cog(Titles(bot))
    print("Titles Cog Loaded!")
