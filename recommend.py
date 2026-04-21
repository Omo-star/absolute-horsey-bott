import datetime
import json
import os
from typing import Any

import discord
from discord.ext import commands
from discord import app_commands

from economy_shared import load_state, state
from economy import get_user

load_state()

ROAST_MEMORY_FILE = "roast_memory.json"


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _to_dt(value: Any) -> datetime.datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
        except Exception:
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        # unix timestamp string
        if text.isdigit():
            try:
                return datetime.datetime.fromtimestamp(int(text), tz=datetime.timezone.utc)
            except Exception:
                pass

        # iso date / datetime
        try:
            text = text.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc)
        except Exception:
            return None

    return None


def _same_utc_day(a: datetime.datetime | None, b: datetime.datetime | None) -> bool:
    if not a or not b:
        return False
    return a.date() == b.date()


def _safe_get(d: dict, *keys, default=None):
    for key in keys:
        if key in d:
            return d[key]
    return default


def _first_number(d: dict, *keys, default=0) -> float:
    for key in keys:
        if key in d:
            try:
                return float(d[key])
            except Exception:
                continue
    return float(default)


def _raw_user_record(uid: int) -> dict:
    uid_s = str(uid)

    candidate_roots = [
        state.get("users", {}),
        state.get("profiles", {}),
        state.get("players", {}),
        state.get("economy_users", {}),
    ]

    for root in candidate_roots:
        if isinstance(root, dict):
            if uid in root and isinstance(root[uid], dict):
                return root[uid]
            if uid_s in root and isinstance(root[uid_s], dict):
                return root[uid_s]

    return {}


def _has_profile(uid: int) -> bool:
    raw = _raw_user_record(uid)
    if raw:
        return True

    # fallback: if your economy system creates records lazily, try to detect
    # whether the user looks initialized beyond an empty skeleton
    try:
        user = get_user(uid)
        if not isinstance(user, dict):
            return False

        interesting_keys = {
            "balance", "money", "cash", "horsenncy",
            "inventory", "team", "creatures", "profile_created",
            "last_daily", "quests", "titles"
        }
        return any(k in user for k in interesting_keys)
    except Exception:
        return False


def _get_user_data(uid: int) -> dict:
    try:
        data = get_user(uid)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _daily_claimed_today(user: dict) -> bool:
    now = _now_utc()

    possible_fields = [
        "last_daily",
        "daily_last_claim",
        "daily_claimed_at",
        "daily_ts",
        "daily_timestamp",
        "last_daily_claim",
    ]

    for field in possible_fields:
        dt = _to_dt(user.get(field))
        if _same_utc_day(dt, now):
            return True

    cooldown_until = _to_dt(
        _safe_get(user, "daily_cooldown_until", "daily_reset_at", "next_daily_at")
    )
    if cooldown_until and cooldown_until > now:
        # if daily is on cooldown, assume it was already claimed
        return True

    return False


def _current_money(user: dict) -> int:
    return int(_first_number(
        user,
        "balance",
        "money",
        "cash",
        "wallet",
        "horsenncy",
        default=0
    ))


def _get_team_list(user: dict) -> list:
    candidates = [
        user.get("team"),
        user.get("party"),
        user.get("active_team"),
        user.get("team_members"),
        user.get("equipped_team"),
    ]

    for value in candidates:
        if isinstance(value, list):
            return value

    # sometimes team is nested
    creatures = user.get("creatures")
    if isinstance(creatures, dict):
        maybe_team = creatures.get("team")
        if isinstance(maybe_team, list):
            return maybe_team

    return []


def _has_team(user: dict) -> bool:
    return len(_get_team_list(user)) > 0


def _battled_today(user: dict) -> bool:
    now = _now_utc()

    possible_fields = [
        "last_battle",
        "battle_last_played",
        "battle_ts",
        "last_battle_at",
        "battle_today_at",
    ]

    for field in possible_fields:
        dt = _to_dt(user.get(field))
        if _same_utc_day(dt, now):
            return True

    # if you track count instead of timestamp
    daily_counts = [
        user.get("battles_today"),
        user.get("daily_battles"),
        user.get("battle_count_today"),
    ]
    for value in daily_counts:
        try:
            if int(value) > 0:
                return True
        except Exception:
            pass

    return False


def _load_roast_memory() -> dict:
    if not os.path.exists(ROAST_MEMORY_FILE):
        return {}
    try:
        with open(ROAST_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _is_ai_heavy(uid: int) -> bool:
    mem = _load_roast_memory()
    user_memory = mem.get("user_memory", {})
    profile = user_memory.get(str(uid), {})
    isec = profile.get("IS", {}) if isinstance(profile, dict) else {}

    roast_requests = int(isec.get("roast_requests", 0) or 0)
    bot_mentions = int(isec.get("bot_mentions", 0) or 0)
    self_roasts = int(isec.get("self_roasts", 0) or 0)

    score = roast_requests + bot_mentions + self_roasts
    return score >= 5


def _build_recommendations(uid: int) -> list[dict]:
    recs: list[dict] = []

    has_profile = _has_profile(uid)
    user = _get_user_data(uid) if has_profile else {}

    if not has_profile:
        recs.append({
            "key": "profile",
            "priority": 100,
            "title": "start with `/profile`",
            "reason": "you need an account shell before the rest of the progression feels good.",
            "category": "start"
        })
        recs.append({
            "key": "start",
            "priority": 95,
            "title": "then run `/start`",
            "reason": "that will push you into the cleanest route instead of dumping you into the whole command list.",
            "category": "start"
        })
        return sorted(recs, key=lambda x: x["priority"], reverse=True)

    daily_done = _daily_claimed_today(user)
    money = _current_money(user)
    has_team = _has_team(user)
    battled_today = _battled_today(user)
    ai_heavy = _is_ai_heavy(uid)

    if not daily_done:
        recs.append({
            "key": "daily",
            "priority": 92,
            "title": "claim `/daily`",
            "reason": "free money is usually the best first click each day.",
            "category": "economy"
        })

    if money < 250:
        recs.append({
            "key": "work",
            "priority": 84,
            "title": "do `/work`",
            "reason": f"your current money looks low ({money}), so a quick income command is the cleanest next move.",
            "category": "economy"
        })

    if not has_team:
        recs.append({
            "key": "hunt",
            "priority": 88,
            "title": "build a team with `/hunt` or `/fish`",
            "reason": "you do not look like you have an active team yet, so adventure progression is blocked behind that.",
            "category": "adventure"
        })
        recs.append({
            "key": "team_list",
            "priority": 70,
            "title": "after that, open `/team list`",
            "reason": "once you get a creature, checking team setup is the next clean step.",
            "category": "adventure"
        })
    else:
        recs.append({
            "key": "team_list",
            "priority": 62,
            "title": "check `/team list`",
            "reason": "you already have a team, so it is worth seeing what you are actually bringing.",
            "category": "adventure"
        })

        if not battled_today:
            recs.append({
                "key": "battle",
                "priority": 82,
                "title": "run `/battle`",
                "reason": "you have a team but do not look like you have battled today yet.",
                "category": "adventure"
            })

    if ai_heavy:
        recs.append({
            "key": "roast",
            "priority": 60,
            "title": "try `/roast` or tweak `/roastmode`",
            "reason": "you look like one of your ai-heavy users, so it makes sense to surface the bot’s personality side too.",
            "category": "ai"
        })
        recs.append({
            "key": "code_list",
            "priority": 54,
            "title": "open `/code_list` or try `/hack`",
            "reason": "those fit the same ai/utility lane and give variety beyond roast mode.",
            "category": "ai"
        })

    # fallback recommendations if nothing urgent is missing
    if not recs:
        recs.extend([
            {
                "key": "quests",
                "priority": 58,
                "title": "check `/quests`",
                "reason": "when your core basics are handled, quests are the best general-purpose progress pointer.",
                "category": "deep"
            },
            {
                "key": "dungeon",
                "priority": 52,
                "title": "jump into `/dungeon`, `/voidmaze`, or `/arena`",
                "reason": "that is where your higher-depth progression starts to feel different from a basic economy bot.",
                "category": "deep"
            },
            {
                "key": "help",
                "priority": 45,
                "title": "open `/help deep` or `/help adventure`",
                "reason": "that is the fastest way to branch into a system you have not touched much yet.",
                "category": "help"
            }
        ])

    # de-duplicate by key, keep highest priority
    best_by_key: dict[str, dict] = {}
    for rec in recs:
        key = rec["key"]
        if key not in best_by_key or rec["priority"] > best_by_key[key]["priority"]:
            best_by_key[key] = rec

    return sorted(best_by_key.values(), key=lambda x: x["priority"], reverse=True)


def _make_recommend_embed(user: discord.abc.User, recs: list[dict]) -> discord.Embed:
    top = recs[0]

    embed = discord.Embed(
        title="🧭 what’s next",
        description=f"best next move for {user.mention}: **{top['title']}**",
        color=discord.Color.blurple(),
        timestamp=_now_utc()
    )

    embed.add_field(
        name="why this came first",
        value=top["reason"],
        inline=False
    )

    others = recs[1:4]
    if others:
        embed.add_field(
            name="after that",
            value="\n".join(f"• **{r['title']}** — {r['reason']}" for r in others),
            inline=False
        )

    category_counts: dict[str, int] = {}
    for r in recs:
        category_counts[r["category"]] = category_counts.get(r["category"], 0) + 1

    summary_bits = []
    for cat in ("start", "economy", "adventure", "ai", "deep", "help"):
        if category_counts.get(cat):
            summary_bits.append(f"{cat}: {category_counts[cat]}")

    if summary_bits:
        embed.add_field(
            name="what this is looking at",
            value=" | ".join(summary_bits),
            inline=False
        )

    embed.set_footer(text="use /recommend any time you want the bot to point you somewhere useful")
    return embed


class Recommend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send_recommendation(self, interaction: discord.Interaction):
        recs = _build_recommendations(interaction.user.id)
        embed = _make_recommend_embed(interaction.user, recs)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="recommend", description="Get the best next command for your current progress.")
    async def recommend(self, interaction: discord.Interaction):
        await self._send_recommendation(interaction)

    @app_commands.command(name="whatsnext", description="See the smartest next things to do in FuSBot.")
    async def whatsnext(self, interaction: discord.Interaction):
        await self._send_recommendation(interaction)


async def setup(bot):
    print("Loading Recommend Cog...")
    await bot.add_cog(Recommend(bot))
    print("Recommend Cog Loaded!")
