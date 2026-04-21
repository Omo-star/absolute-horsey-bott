import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user
from economy_shared import state

try:
    from economy import STOCKS
except Exception:
    STOCKS = {}


def utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts)
    except Exception:
        return None


def format_remaining(ts) -> str:
    dt = parse_iso(ts)
    if not dt:
        return "Ready"

    remaining = dt - utcnow()
    if remaining.total_seconds() <= 0:
        return "Ready"

    total = int(remaining.total_seconds())
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def format_bool(value: bool) -> str:
    return "Yes" if value else "No"


def cooldown_from_last(ts, delta: datetime.timedelta):
    dt = parse_iso(ts)
    if not dt:
        return "Ready"
    return format_remaining((dt + delta).isoformat())


def get_wealth_rank(user_id: int):
    users = state.get("users", {})
    if not users:
        return None, 0

    ranking = sorted(
        users.items(),
        key=lambda x: x[1].get("balance", 0),
        reverse=True
    )

    total = len(ranking)
    for idx, (uid, _) in enumerate(ranking, start=1):
        if uid == str(user_id):
            return idx, total

    return None, total


def portfolio_value(portfolio: dict) -> int:
    total = 0
    for symbol, amount in portfolio.items():
        if symbol in STOCKS:
            total += STOCKS[symbol].get("price", 0) * amount
    return total


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your FuSBot account profile.")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        data = get_user(target.id)

        balance = data.get("balance", 0)
        pray_points = data.get("pray", 0)
        inventory = data.get("inventory", {})
        owned_animals = data.get("owned_animals", [])
        team = data.get("team", [])
        stocks = data.get("stocks", {})
        dungeon = data.get("dungeon", {})
        raid = data.get("raid", {})
        pvp = data.get("pvp", {})
        roast_protection_until = parse_iso(data.get("roast_protection_until"))

        inv_unique = sum(1 for qty in inventory.values() if qty > 0)
        inv_total = sum(max(0, qty) for qty in inventory.values())
        team_power = sum(animal.get("strength", 0) for animal in team)
        stock_value = portfolio_value(stocks)
        wealth_rank, ranked_users = get_wealth_rank(target.id)

        embed = discord.Embed(
            title=f"📜 {target.display_name}'s FuSBot Profile",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )

        embed.set_thumbnail(url=target.display_avatar.url)

        if wealth_rank:
            economy_block = (
                f"💴 **Balance:** `{balance:,}` horsenncy\n"
                f"🙏 **Prayer Points:** `{pray_points}`\n"
                f"🏆 **Wealth Rank:** `#{wealth_rank}` / `{ranked_users}`"
            )
        else:
            economy_block = (
                f"💴 **Balance:** `{balance:,}` horsenncy\n"
                f"🙏 **Prayer Points:** `{pray_points}`\n"
                f"🏆 **Wealth Rank:** `Unranked`"
            )
        embed.add_field(name="Economy", value=economy_block, inline=False)

        collect_block = (
            f"🎒 **Inventory:** `{inv_total}` items across `{inv_unique}` unique entries\n"
            f"🦌 **Owned Animals:** `{len(owned_animals)}`\n"
            f"🛡️ **Team Size:** `{len(team)}` / `8`\n"
            f"⚔️ **Team Power:** `{team_power:,}`"
        )
        embed.add_field(name="Collection", value=collect_block, inline=False)

        stocks_block = (
            f"📈 **Owned Stocks:** `{len(stocks)}` symbols\n"
            f"💼 **Portfolio Value:** `{stock_value:,}` horsenncy"
        )
        embed.add_field(name="Market", value=stocks_block, inline=False)

        dungeon_block = (
            f"🏰 **Active Run:** `{format_bool(dungeon.get('active', False))}`\n"
            f"🧱 **Floor:** `{dungeon.get('floor', 1)}`\n"
            f"❤️ **HP:** `{dungeon.get('hp', 100)}` / `{dungeon.get('max_hp', 100)}`\n"
            f"⚡ **Energy:** `{dungeon.get('energy', 3)}`\n"
            f"🪬 **Relics:** `{len(dungeon.get('relics', []))}`\n"
            f"☠️ **Curses:** `{len(dungeon.get('curses', []))}`"
        )
        embed.add_field(name="Dungeon", value=dungeon_block, inline=False)

        raid_block = (
            f"⚔️ **Joined Raid:** `{format_bool(raid.get('joined', False))}`\n"
            f"💥 **Raid Damage:** `{raid.get('damage', 0):,}`\n"
            f"🧿 **Relic Bonus:** `{raid.get('relic_bonus', 0)}`\n"
            f"🛡️ **PvP Defense Bonus:** `{pvp.get('defense_bonus', 0)}`\n"
            f"🗡️ **PvP Offense Bonus:** `{pvp.get('offense_bonus', 0)}`"
        )
        embed.add_field(name="Combat", value=raid_block, inline=False)

        cooldown_block = (
            f"🎁 **Daily:** `{cooldown_from_last(data.get('last_daily'), datetime.timedelta(days=1))}`\n"
            f"💼 **Work:** `{cooldown_from_last(data.get('last_work'), datetime.timedelta(hours=1))}`\n"
            f"🙏 **Pray:** `{cooldown_from_last(data.get('last_pray'), datetime.timedelta(minutes=10))}`\n"
            f"🎣 **Fish:** `{format_remaining(data.get('fish_cooldown'))}`\n"
            f"🏹 **Hunt:** `{format_remaining(data.get('hunt_cooldown'))}`"
        )
        embed.add_field(name="Cooldowns", value=cooldown_block, inline=False)

        optional_lines = []

        arena = data.get("arena")
        if isinstance(arena, dict) and arena:
            optional_lines.append(
                f"🏟️ Arena — Rating `{arena.get('rating', 0)}`, XP `{arena.get('xp', 0)}`, Crowns `{arena.get('crowns', 0)}`"
            )

        voidmaze = data.get("voidmaze")
        if isinstance(voidmaze, dict) and voidmaze:
            optional_lines.append(
                f"🌀 Voidmaze — Best Depth `{voidmaze.get('best_depth', 0)}`, Streak `{voidmaze.get('streak', 0)}`"
            )

        lab = data.get("lab")
        if isinstance(lab, dict) and lab:
            optional_lines.append(
                f"🧪 Lab — Level `{lab.get('level', 0)}`, XP `{lab.get('xp', 0)}`, Stability `{lab.get('stability', 0)}`"
            )

        hack = data.get("hack")
        if isinstance(hack, dict) and hack:
            optional_lines.append(
                f"🛠️ Hack — Skill `{hack.get('skill', 0)}`, Rep `{hack.get('reputation', 0)}`, Trace `{hack.get('trace', 0)}`"
            )

        if optional_lines:
            embed.add_field(name="Extra Systems", value="\n".join(optional_lines), inline=False)

        if roast_protection_until and roast_protection_until > utcnow():
            protect_text = roast_protection_until.strftime("%Y-%m-%d %H:%M UTC")
        else:
            protect_text = "Inactive"

        embed.add_field(
            name="Roast Status",
            value=f"🛡️ **Protection:** `{protect_text}`",
            inline=False
        )

        embed.set_footer(text="FuSBot profile • use /inventory, /team, /stocks, or /dungeon for deeper info")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    print("Loading Profile Cog...")
    await bot.add_cog(Profile(bot))
    print("Profile Cog Loaded!")
