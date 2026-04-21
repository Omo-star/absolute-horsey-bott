import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user

try:
    from achievement import build_snapshot
except Exception:
    build_snapshot = None


def rarity_counts(animals):
    counts = {}
    if not isinstance(animals, list):
        return counts
    for animal in animals:
        if isinstance(animal, dict):
            rarity = str(animal.get("rarity") or animal.get("tier") or "unknown").lower()
        else:
            rarity = "unknown"
        counts[rarity] = counts.get(rarity, 0) + 1
    return counts


def compact_dict_lines(d: dict, limit: int = 12):
    if not d:
        return "none"
    items = sorted(d.items(), key=lambda x: (-x[1], x[0]))[:limit]
    return "\n".join(f"• {k}: `{v}`" for k, v in items)


class Collections(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="collections", description="View your collection progress.")
    async def collections(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        data = get_user(target.id)
        snapshot = build_snapshot(target.id, data) if build_snapshot else None

        inventory = data.get("inventory", {}) if isinstance(data.get("inventory", {}), dict) else {}
        owned_animals = data.get("owned_animals", []) if isinstance(data.get("owned_animals", []), list) else []
        team = data.get("team", []) if isinstance(data.get("team", []), list) else []
        dungeon = data.get("dungeon", {}) if isinstance(data.get("dungeon", {}), dict) else {}
        voidmaze = data.get("voidmaze", {}) if isinstance(data.get("voidmaze", {}), dict) else {}
        lab = data.get("lab", {}) if isinstance(data.get("lab", {}), dict) else {}
        stocks = data.get("stocks", {}) if isinstance(data.get("stocks", {}), dict) else {}

        inv_unique = sum(1 for qty in inventory.values() if int(qty or 0) > 0)
        inv_total = sum(max(0, int(qty or 0)) for qty in inventory.values())
        animal_counts = rarity_counts(owned_animals)
        team_power = sum(int(animal.get("strength", 0) or 0) for animal in team if isinstance(animal, dict))
        relics = dungeon.get("relics", []) if isinstance(dungeon.get("relics", []), list) else []
        curses = dungeon.get("curses", []) if isinstance(dungeon.get("curses", []), list) else []
        artifacts = voidmaze.get("artifacts", []) if isinstance(voidmaze.get("artifacts", []), list) else []
        breakthroughs = lab.get("breakthroughs", []) if isinstance(lab.get("breakthroughs", []), list) else []
        stock_symbols = sum(1 for _, amount in stocks.items() if int(amount or 0) > 0)

        embed = discord.Embed(
            title=f"📚 {target.display_name}'s Collections",
            description="your account-wide collector board",
            color=discord.Color.teal(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="Inventory",
            value=(
                f"total items: `{inv_total}`\n"
                f"unique entries: `{inv_unique}`\n"
                f"top items:\n{compact_dict_lines({k: int(v or 0) for k, v in inventory.items() if int(v or 0) > 0})}"
            ),
            inline=False
        )

        embed.add_field(
            name="Animals",
            value=(
                f"owned animals: `{len(owned_animals)}`\n"
                f"team size: `{len(team)}`\n"
                f"team power: `{team_power}`\n"
                f"rarities:\n{compact_dict_lines(animal_counts)}"
            ),
            inline=False
        )

        embed.add_field(
            name="Special Finds",
            value=(
                f"dungeon relics: `{len(relics)}`\n"
                f"dungeon curses: `{len(curses)}`\n"
                f"void artifacts: `{len(artifacts)}`\n"
                f"lab breakthroughs: `{len(breakthroughs)}`\n"
                f"stock symbols owned: `{stock_symbols}`"
            ),
            inline=False
        )

        if snapshot:
            embed.add_field(
                name="Collector Grade",
                value=(
                    f"inventory score base: `{snapshot['inventory_unique']}`\n"
                    f"animal count: `{snapshot['owned_animals_count']}`\n"
                    f"legendary+ animals: `{snapshot['legendary_plus_animals']}`\n"
                    f"strongest team member: `{snapshot['strongest_team_member_name']}`"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    print("Loading Collections Cog...")
    await bot.add_cog(Collections(bot))
    print("Collections Cog Loaded!")
