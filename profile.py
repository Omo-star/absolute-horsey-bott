import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user

try:
    from achievement import get_profile_meta, format_mastery_block, format_next_up, format_rare_unlocks
except Exception:
    get_profile_meta = None
    format_mastery_block = None
    format_next_up = None
    format_rare_unlocks = None


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


def cooldown_from_last(ts, delta: datetime.timedelta):
    dt = parse_iso(ts)
    if not dt:
        return "Ready"
    return format_remaining((dt + delta).isoformat())


def bool_text(value: bool) -> str:
    return "Yes" if value else "No"


def protect_text(ts) -> str:
    dt = parse_iso(ts) if not isinstance(ts, datetime.datetime) else ts
    if dt and dt > utcnow():
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    return "Inactive"


def compact_number(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000_000:
        return f"{sign}{n / 1_000_000_000:.1f}b"
    if n >= 1_000_000:
        return f"{sign}{n / 1_000_000:.1f}m"
    if n >= 1_000:
        return f"{sign}{n / 1_000:.1f}k"
    return f"{sign}{n}"


def fallback_meta(user_id: int, data: dict):
    balance = int(data.get("balance", 0) or 0)
    pray_points = int(data.get("pray", 0) or 0)
    inventory = data.get("inventory", {}) if isinstance(data.get("inventory", {}), dict) else {}
    owned_animals = data.get("owned_animals", []) if isinstance(data.get("owned_animals", []), list) else []
    team = data.get("team", []) if isinstance(data.get("team", []), list) else []
    dungeon = data.get("dungeon", {}) if isinstance(data.get("dungeon", {}), dict) else {}
    raid = data.get("raid", {}) if isinstance(data.get("raid", {}), dict) else {}
    arena = data.get("arena", {}) if isinstance(data.get("arena", {}), dict) else {}
    voidmaze = data.get("voidmaze", {}) if isinstance(data.get("voidmaze", {}), dict) else {}
    lab = data.get("lab", {}) if isinstance(data.get("lab", {}), dict) else {}
    hack = data.get("hack", {}) if isinstance(data.get("hack", {}), dict) else {}
    team_power = sum(int(animal.get("strength", 0) or 0) for animal in team if isinstance(animal, dict))
    snapshot = {
        "balance": balance,
        "pray_points": pray_points,
        "net_worth": balance,
        "inventory_unique": sum(1 for qty in inventory.values() if int(qty or 0) > 0),
        "inventory_total": sum(max(0, int(qty or 0)) for qty in inventory.values()),
        "owned_animals_count": len(owned_animals),
        "legendary_plus_animals": 0,
        "team_size": len(team),
        "team_power": team_power,
        "strongest_team_member_name": "None",
        "strongest_team_member_power": 0,
        "stock_symbols": 0,
        "stock_value": 0,
        "wealth_rank": None,
        "ranked_users": 0,
        "dungeon_active": bool(dungeon.get("active", False)),
        "dungeon_floor": int(dungeon.get("floor", 1) or 1),
        "dungeon_hp": int(dungeon.get("hp", 100) or 100),
        "dungeon_max_hp": int(dungeon.get("max_hp", 100) or 100),
        "dungeon_energy": int(dungeon.get("energy", 3) or 3),
        "dungeon_relics": len(dungeon.get("relics", [])) if isinstance(dungeon.get("relics", []), list) else 0,
        "dungeon_curses": len(dungeon.get("curses", [])) if isinstance(dungeon.get("curses", []), list) else 0,
        "raid_joined": bool(raid.get("joined", False)),
        "raid_damage": int(raid.get("damage", 0) or 0),
        "raid_relic_bonus": int(raid.get("relic_bonus", 0) or 0),
        "pvp_offense_bonus": int(data.get("pvp", {}).get("offense_bonus", 0) or 0) if isinstance(data.get("pvp", {}), dict) else 0,
        "pvp_defense_bonus": int(data.get("pvp", {}).get("defense_bonus", 0) or 0) if isinstance(data.get("pvp", {}), dict) else 0,
        "arena_rating": int(arena.get("rating", 0) or 0),
        "arena_xp": int(arena.get("xp", 0) or 0),
        "arena_crowns": int(arena.get("crowns", 0) or 0),
        "void_best_depth": int(voidmaze.get("best_depth", 0) or 0),
        "void_streak": int(voidmaze.get("streak", 0) or 0),
        "void_artifacts": len(voidmaze.get("artifacts", [])) if isinstance(voidmaze.get("artifacts", []), list) else 0,
        "void_fragments": int(voidmaze.get("fragments", 0) or 0),
        "void_keys": int(voidmaze.get("keys", 0) or 0),
        "lab_level": int(lab.get("level", 0) or 0),
        "lab_xp": int(lab.get("xp", 0) or 0),
        "lab_stability": int(lab.get("stability", 0) or 0),
        "lab_breakthroughs": len(lab.get("breakthroughs", [])) if isinstance(lab.get("breakthroughs", []), list) else 0,
        "hack_skill": int(hack.get("skill", 0) or 0),
        "hack_reputation": int(hack.get("reputation", 0) or 0),
        "hack_trace": int(hack.get("trace", 0) or 0),
        "active_modes": sum(1 for x in [balance > 0, len(inventory) > 0, len(owned_animals) > 0, bool(arena), bool(voidmaze), bool(lab), bool(hack)] if x),
        "ready_cooldowns": sum(
            1
            for value in [
                cooldown_from_last(data.get("last_daily"), datetime.timedelta(days=1)),
                cooldown_from_last(data.get("last_work"), datetime.timedelta(hours=1)),
                cooldown_from_last(data.get("last_pray"), datetime.timedelta(minutes=10)),
                format_remaining(data.get("fish_cooldown")),
                format_remaining(data.get("hunt_cooldown")),
            ]
            if value == "Ready"
        ),
        "roast_protection_until": parse_iso(data.get("roast_protection_until")),
    }
    return {
        "snapshot": snapshot,
        "summary": {"unlocked_count": 0, "total_count": 0, "completion": 0, "total_points": 0},
        "title": "fresh spawn",
        "grades": [],
        "next_up": [],
        "rare_unlocked": [],
    }


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your FuSBot account profile.")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        data = get_user(target.id)
        meta = get_profile_meta(target.id, data) if get_profile_meta else fallback_meta(target.id, data)
        snapshot = meta["snapshot"]
        summary = meta["summary"]
        grades = meta["grades"]

        embed = discord.Embed(
            title=f"📜 {target.display_name} — {meta['title']}",
            description=(
                f"**Achievements:** `{summary['unlocked_count']}` / `{summary['total_count']}`"
                if summary["total_count"]
                else "**Achievements:** `not loaded yet`"
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        wealth_text = f"`#{snapshot['wealth_rank']}` / `{snapshot['ranked_users']}`" if snapshot.get("wealth_rank") else "`Unranked`"
        overview_block = (
            f"💎 **Net Worth:** `{snapshot['net_worth']:,}` horsenncy\n"
            f"🏆 **Wealth Rank:** {wealth_text}\n"
            f"🎖️ **Achievement Points:** `{summary['total_points']}`\n"
            f"📊 **Completion:** `{summary['completion']}%`\n"
            f"🧩 **Active Modes:** `{snapshot['active_modes']}`"
        )
        embed.add_field(name="Overview", value=overview_block, inline=False)

        economy_block = (
            f"💴 **Balance:** `{snapshot['balance']:,}` horsenncy\n"
            f"📈 **Stocks Owned:** `{snapshot['stock_symbols']}` symbols\n"
            f"💼 **Portfolio Value:** `{snapshot['stock_value']:,}` horsenncy\n"
            f"🙏 **Prayer Points:** `{snapshot['pray_points']}`"
        )
        embed.add_field(name="Economy", value=economy_block, inline=False)

        collection_block = (
            f"🎒 **Inventory:** `{snapshot['inventory_total']}` items across `{snapshot['inventory_unique']}` entries\n"
            f"🦌 **Owned Animals:** `{snapshot['owned_animals_count']}`\n"
            f"🌌 **Legendary+ Animals:** `{snapshot['legendary_plus_animals']}`\n"
            f"🛡️ **Team Size:** `{snapshot['team_size']}` / `8`\n"
            f"⚔️ **Team Power:** `{snapshot['team_power']:,}`\n"
            f"👑 **Strongest Unit:** `{snapshot['strongest_team_member_name']}` ({compact_number(snapshot['strongest_team_member_power'])})"
        )
        embed.add_field(name="Collection", value=collection_block, inline=False)

        progression_block = (
            f"🏰 **Dungeon:** Floor `{snapshot['dungeon_floor']}` • HP `{snapshot['dungeon_hp']}`/`{snapshot['dungeon_max_hp']}` • Energy `{snapshot['dungeon_energy']}`\n"
            f"⚔️ **Raid:** Damage `{snapshot['raid_damage']:,}` • Joined `{bool_text(snapshot['raid_joined'])}`\n"
            f"🏟️ **Arena:** Rating `{snapshot['arena_rating']}` • Crowns `{snapshot['arena_crowns']}`\n"
            f"🌀 **Voidmaze:** Best Depth `{snapshot['void_best_depth']}` • Streak `{snapshot['void_streak']}`\n"
            f"🧪 **Lab:** Level `{snapshot['lab_level']}` • Breakthroughs `{snapshot['lab_breakthroughs']}`\n"
            f"🛠️ **Hack:** Skill `{snapshot['hack_skill']}` • Rep `{snapshot['hack_reputation']}` • Trace `{snapshot['hack_trace']}`"
        )
        embed.add_field(name="Progression", value=progression_block, inline=False)

        if grades and format_mastery_block:
            embed.add_field(name="Masteries", value=format_mastery_block(grades), inline=False)

        if meta.get("rare_unlocked") and format_rare_unlocks:
            embed.add_field(name="Rare Unlocks", value=format_rare_unlocks(meta["rare_unlocked"]), inline=False)

        if meta.get("next_up") and format_next_up:
            embed.add_field(name="Next Up", value=format_next_up(meta["next_up"]), inline=False)

        cooldown_block = (
            f"🎁 **Daily:** `{cooldown_from_last(data.get('last_daily'), datetime.timedelta(days=1))}`\n"
            f"💼 **Work:** `{cooldown_from_last(data.get('last_work'), datetime.timedelta(hours=1))}`\n"
            f"🙏 **Pray:** `{cooldown_from_last(data.get('last_pray'), datetime.timedelta(minutes=10))}`\n"
            f"🎣 **Fish:** `{format_remaining(data.get('fish_cooldown'))}`\n"
            f"🏹 **Hunt:** `{format_remaining(data.get('hunt_cooldown'))}`\n"
            f"✅ **Ready Count:** `{snapshot['ready_cooldowns']}` / `5`"
        )
        embed.add_field(name="Cooldowns", value=cooldown_block, inline=False)

        status_block = (
            f"🛡️ **Roast Protection:** `{protect_text(snapshot.get('roast_protection_until') or data.get('roast_protection_until'))}`\n"
            f"🪬 **Dungeon Relics:** `{snapshot['dungeon_relics']}`\n"
            f"☠️ **Dungeon Curses:** `{snapshot['dungeon_curses']}`\n"
            f"🧿 **Raid Relic Bonus:** `{snapshot['raid_relic_bonus']}`\n"
            f"🗡️ **PvP Offense Bonus:** `{snapshot['pvp_offense_bonus']}`\n"
            f"🛡️ **PvP Defense Bonus:** `{snapshot['pvp_defense_bonus']}`"
        )
        embed.add_field(name="Status", value=status_block, inline=False)

        embed.set_footer(text="FuSBot profile • use /achievements for the full unlock board")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    print("Loading Profile Cog...")
    await bot.add_cog(Profile(bot))
    print("Profile Cog Loaded!")
