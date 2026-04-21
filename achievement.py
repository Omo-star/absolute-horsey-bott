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


TIER_ORDER = ["common", "rare", "epic", "legendary", "mythic"]
TIER_LABELS = {
    "common": "Common",
    "rare": "Rare",
    "epic": "Epic",
    "legendary": "Legendary",
    "mythic": "Mythic",
}
TIER_POINTS = {
    "common": 5,
    "rare": 10,
    "epic": 20,
    "legendary": 35,
    "mythic": 60,
}
TIER_EMOJIS = {
    "common": "⚪",
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🔴",
}


def utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts)
    except Exception:
        return None


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def lenish(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (list, tuple, set, dict, str)):
        return len(value)
    return safe_int(value, 0)


def format_compact(n: int) -> str:
    n = safe_int(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000_000:
        return f"{sign}{n / 1_000_000_000:.1f}b"
    if n >= 1_000_000:
        return f"{sign}{n / 1_000_000:.1f}m"
    if n >= 1_000:
        return f"{sign}{n / 1_000:.1f}k"
    return f"{sign}{n}"


def cap_percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def portfolio_value(portfolio: dict) -> int:
    total = 0
    if not isinstance(portfolio, dict):
        return 0
    for symbol, amount in portfolio.items():
        if symbol in STOCKS:
            total += safe_int(STOCKS[symbol].get("price", 0)) * max(0, safe_int(amount))
    return total


def get_wealth_rank(user_id: int):
    users = state.get("users", {})
    if not users:
        return None, 0
    ranking = sorted(users.items(), key=lambda x: x[1].get("balance", 0), reverse=True)
    total = len(ranking)
    for idx, (uid, _) in enumerate(ranking, start=1):
        if uid == str(user_id):
            return idx, total
    return None, total


def first_nonempty(*values):
    for value in values:
        if value not in (None, "", [], {}, ()):
            return value
    return None


def normalize_rarity(value: str) -> str:
    if not value:
        return "unknown"
    text = str(value).strip().lower()
    aliases = {
        "uncommon": "uncommon",
        "common": "common",
        "rare": "rare",
        "epic": "epic",
        "legendary": "legendary",
        "mythic": "mythic",
        "cosmic": "cosmic",
        "god": "god",
        "divine": "god",
        "celestial": "cosmic",
    }
    return aliases.get(text, text)


def count_animal_rarities(animals):
    counts = {}
    if not isinstance(animals, list):
        return counts
    for animal in animals:
        if isinstance(animal, dict):
            rarity = normalize_rarity(first_nonempty(animal.get("rarity"), animal.get("tier")))
        else:
            rarity = "unknown"
        counts[rarity] = counts.get(rarity, 0) + 1
    return counts


def strongest_member(team):
    if not isinstance(team, list) or not team:
        return None
    best = None
    best_strength = -1
    for animal in team:
        if not isinstance(animal, dict):
            continue
        strength = safe_int(animal.get("strength", 0))
        if strength > best_strength:
            best_strength = strength
            best = animal
    return best


def name_of_animal(animal):
    if not isinstance(animal, dict):
        return "None"
    return str(first_nonempty(animal.get("name"), animal.get("species"), animal.get("type"), animal.get("title"), "Unknown"))


def count_ready_cooldowns(data: dict) -> int:
    ready = 0
    now = utcnow()
    checks = [
        (data.get("last_daily"), datetime.timedelta(days=1), False),
        (data.get("last_work"), datetime.timedelta(hours=1), False),
        (data.get("last_pray"), datetime.timedelta(minutes=10), False),
        (data.get("fish_cooldown"), None, True),
        (data.get("hunt_cooldown"), None, True),
    ]
    for ts, delta, absolute in checks:
        dt = parse_iso(ts)
        if not dt:
            ready += 1
            continue
        if absolute:
            if dt <= now:
                ready += 1
        else:
            if dt + delta <= now:
                ready += 1
    return ready


def build_snapshot(user_id: int, data: dict | None = None) -> dict:
    data = data or get_user(user_id)

    balance = safe_int(data.get("balance", 0))
    pray_points = safe_int(data.get("pray", 0))
    inventory = data.get("inventory", {}) if isinstance(data.get("inventory", {}), dict) else {}
    owned_animals = data.get("owned_animals", []) if isinstance(data.get("owned_animals", []), list) else []
    team = data.get("team", []) if isinstance(data.get("team", []), list) else []
    stocks = data.get("stocks", {}) if isinstance(data.get("stocks", {}), dict) else {}
    dungeon = data.get("dungeon", {}) if isinstance(data.get("dungeon", {}), dict) else {}
    raid = data.get("raid", {}) if isinstance(data.get("raid", {}), dict) else {}
    pvp = data.get("pvp", {}) if isinstance(data.get("pvp", {}), dict) else {}
    arena = data.get("arena", {}) if isinstance(data.get("arena", {}), dict) else {}
    voidmaze = data.get("voidmaze", {}) if isinstance(data.get("voidmaze", {}), dict) else {}
    lab = data.get("lab", {}) if isinstance(data.get("lab", {}), dict) else {}
    hack = data.get("hack", {}) if isinstance(data.get("hack", {}), dict) else {}

    inv_unique = sum(1 for qty in inventory.values() if safe_int(qty) > 0)
    inv_total = sum(max(0, safe_int(qty)) for qty in inventory.values())
    team_power = sum(max(0, safe_int(animal.get("strength", 0))) for animal in team if isinstance(animal, dict))
    stock_value = portfolio_value(stocks)
    stock_symbols = sum(1 for _, amount in stocks.items() if safe_int(amount) > 0)
    wealth_rank, ranked_users = get_wealth_rank(user_id)
    roast_protection_until = parse_iso(data.get("roast_protection_until"))
    roast_protection_active = bool(roast_protection_until and roast_protection_until > utcnow())
    animal_rarities = count_animal_rarities(owned_animals)
    strongest = strongest_member(team)
    strongest_power = safe_int(strongest.get("strength", 0)) if isinstance(strongest, dict) else 0
    legendary_plus = sum(animal_rarities.get(k, 0) for k in ("legendary", "mythic", "cosmic", "god"))
    lab_breakthroughs = lenish(first_nonempty(lab.get("breakthroughs"), lab.get("unlocked_breakthroughs"), lab.get("permanent_upgrades")))
    lab_anomalies = lenish(first_nonempty(lab.get("anomalies"), lab.get("active_anomalies")))
    hack_history = lenish(first_nonempty(hack.get("history"), hack.get("runs"), hack.get("recent")))
    void_artifacts = lenish(first_nonempty(voidmaze.get("artifacts"), voidmaze.get("owned_artifacts")))
    void_anomalies = lenish(first_nonempty(voidmaze.get("anomalies"), voidmaze.get("corruptions")))

    active_modes = 0
    mode_checks = [
        balance > 0 or stock_value > 0,
        inv_total > 0,
        len(owned_animals) > 0,
        stock_symbols > 0,
        dungeon.get("active", False) or safe_int(dungeon.get("floor", 1)) > 1,
        safe_int(raid.get("damage", 0)) > 0 or raid.get("joined", False),
        bool(arena),
        bool(voidmaze),
        bool(lab),
        bool(hack),
    ]
    active_modes = sum(1 for x in mode_checks if x)

    return {
        "data": data,
        "user_id": user_id,
        "balance": balance,
        "pray_points": pray_points,
        "inventory": inventory,
        "inventory_unique": inv_unique,
        "inventory_total": inv_total,
        "owned_animals": owned_animals,
        "owned_animals_count": len(owned_animals),
        "animal_rarities": animal_rarities,
        "legendary_plus_animals": legendary_plus,
        "team": team,
        "team_size": len(team),
        "team_power": team_power,
        "strongest_team_member": strongest,
        "strongest_team_member_name": name_of_animal(strongest),
        "strongest_team_member_power": strongest_power,
        "stocks": stocks,
        "stock_symbols": stock_symbols,
        "stock_value": stock_value,
        "net_worth": balance + stock_value,
        "wealth_rank": wealth_rank,
        "ranked_users": ranked_users,
        "dungeon": dungeon,
        "dungeon_floor": safe_int(dungeon.get("floor", 1)),
        "dungeon_active": bool(dungeon.get("active", False)),
        "dungeon_hp": safe_int(dungeon.get("hp", 100)),
        "dungeon_max_hp": max(1, safe_int(dungeon.get("max_hp", 100))),
        "dungeon_energy": safe_int(dungeon.get("energy", 3)),
        "dungeon_relics": lenish(dungeon.get("relics", [])),
        "dungeon_curses": lenish(dungeon.get("curses", [])),
        "dungeon_mutations": lenish(dungeon.get("mutations", [])),
        "raid": raid,
        "raid_joined": bool(raid.get("joined", False)),
        "raid_damage": safe_int(raid.get("damage", 0)),
        "raid_relic_bonus": safe_int(raid.get("relic_bonus", 0)),
        "pvp": pvp,
        "pvp_offense_bonus": safe_int(pvp.get("offense_bonus", 0)),
        "pvp_defense_bonus": safe_int(pvp.get("defense_bonus", 0)),
        "arena": arena,
        "arena_rating": safe_int(arena.get("rating", 0)),
        "arena_xp": safe_int(arena.get("xp", 0)),
        "arena_crowns": safe_int(arena.get("crowns", 0)),
        "voidmaze": voidmaze,
        "void_best_depth": safe_int(voidmaze.get("best_depth", 0)),
        "void_streak": safe_int(voidmaze.get("streak", 0)),
        "void_fragments": safe_int(voidmaze.get("fragments", 0)),
        "void_keys": safe_int(voidmaze.get("keys", 0)),
        "void_artifacts": void_artifacts,
        "void_anomalies": void_anomalies,
        "lab": lab,
        "lab_level": safe_int(lab.get("level", 0)),
        "lab_xp": safe_int(lab.get("xp", 0)),
        "lab_stability": safe_int(lab.get("stability", 0)),
        "lab_breakthroughs": lab_breakthroughs,
        "lab_anomalies": lab_anomalies,
        "hack": hack,
        "hack_skill": safe_int(hack.get("skill", 0)),
        "hack_reputation": safe_int(first_nonempty(hack.get("reputation"), hack.get("rep"), 0)),
        "hack_trace": safe_int(hack.get("trace", 0)),
        "hack_tier": safe_int(first_nonempty(hack.get("tier"), hack.get("skill_tier"), 0)),
        "hack_history": hack_history,
        "roast_protection_active": roast_protection_active,
        "roast_protection_until": roast_protection_until,
        "ready_cooldowns": count_ready_cooldowns(data),
        "active_modes": active_modes,
    }


def system_scores(snapshot: dict) -> dict:
    rare_bonus = snapshot["legendary_plus_animals"] * 6
    economy = min(100.0, snapshot["balance"] / 1500 + snapshot["net_worth"] / 5000 + snapshot["stock_value"] / 2500 + snapshot["pray_points"] * 1.4)
    collection = min(100.0, snapshot["inventory_unique"] * 3 + snapshot["owned_animals_count"] * 1.2 + snapshot["team_size"] * 5 + snapshot["strongest_team_member_power"] / 40 + rare_bonus)
    combat = min(100.0, snapshot["team_power"] / 45 + snapshot["dungeon_floor"] * 2.5 + snapshot["raid_damage"] / 1500 + snapshot["arena_rating"] / 22 + (snapshot["pvp_offense_bonus"] + snapshot["pvp_defense_bonus"]) * 3)
    void = min(100.0, snapshot["void_best_depth"] * 3 + snapshot["void_streak"] * 6 + snapshot["void_artifacts"] * 4 + snapshot["void_fragments"] / 10 + snapshot["void_keys"] * 2)
    research = min(100.0, snapshot["lab_level"] * 8 + snapshot["lab_xp"] / 40 + snapshot["lab_breakthroughs"] * 15 + max(0, snapshot["lab_stability"]) / 5)
    hack = min(100.0, snapshot["hack_skill"] * 9 + snapshot["hack_reputation"] * 1.25 + snapshot["hack_tier"] * 15 + snapshot["hack_history"] * 3 - snapshot["hack_trace"] / 10)
    return {
        "economy": max(0.0, economy),
        "collection": max(0.0, collection),
        "combat": max(0.0, combat),
        "void": max(0.0, void),
        "research": max(0.0, research),
        "hack": max(0.0, hack),
    }


def score_grade(score: float) -> str:
    if score >= 90:
        return "S"
    if score >= 75:
        return "A"
    if score >= 55:
        return "B"
    if score >= 35:
        return "C"
    return "D"


def numeric_progress(snapshot: dict, key: str, target: int, label: str | None = None):
    current = max(0, safe_int(snapshot.get(key, 0)))
    percent = cap_percent((current / target) * 100 if target > 0 else 100)
    name = label or key.replace("_", " ").title()
    return current >= target, percent, f"{name}: {format_compact(current)} / {format_compact(target)}"


def boolean_progress(snapshot: dict, key: str, label: str):
    unlocked = bool(snapshot.get(key))
    return unlocked, 100 if unlocked else 0, label


def achievement_definitions():
    return [
        {"id": "starter_wallet", "name": "Starter Wallet", "emoji": "💴", "tier": "common", "desc": "Hold 100 horsenncy.", "progress": lambda s: numeric_progress(s, "balance", 100, "Balance")},
        {"id": "steady_stash", "name": "Steady Stash", "emoji": "💰", "tier": "common", "desc": "Hold 1,000 horsenncy.", "progress": lambda s: numeric_progress(s, "balance", 1_000, "Balance")},
        {"id": "five_figures", "name": "Five Figures", "emoji": "🏦", "tier": "rare", "desc": "Reach 10,000 balance.", "progress": lambda s: numeric_progress(s, "balance", 10_000, "Balance")},
        {"id": "capital_engine", "name": "Capital Engine", "emoji": "💎", "tier": "epic", "desc": "Reach 100,000 net worth.", "progress": lambda s: numeric_progress(s, "net_worth", 100_000, "Net Worth")},
        {"id": "market_entry", "name": "Market Entry", "emoji": "📈", "tier": "common", "desc": "Own at least 1 stock symbol.", "progress": lambda s: numeric_progress(s, "stock_symbols", 1, "Stock Symbols")},
        {"id": "portfolio_player", "name": "Portfolio Player", "emoji": "💼", "tier": "rare", "desc": "Reach 10,000 portfolio value.", "progress": lambda s: numeric_progress(s, "stock_value", 10_000, "Portfolio")},
        {"id": "prayer_pulse", "name": "Prayer Pulse", "emoji": "🙏", "tier": "common", "desc": "Hold 10 prayer points.", "progress": lambda s: numeric_progress(s, "pray_points", 10, "Prayer")},
        {"id": "divine_static", "name": "Divine Static", "emoji": "⚡", "tier": "rare", "desc": "Hold 50 prayer points.", "progress": lambda s: numeric_progress(s, "pray_points", 50, "Prayer")},
        {"id": "pack_starter", "name": "Pack Starter", "emoji": "🦌", "tier": "common", "desc": "Own 1 animal.", "progress": lambda s: numeric_progress(s, "owned_animals_count", 1, "Animals")},
        {"id": "creature_curator", "name": "Creature Curator", "emoji": "🐾", "tier": "rare", "desc": "Own 25 animals.", "progress": lambda s: numeric_progress(s, "owned_animals_count", 25, "Animals")},
        {"id": "menagerie_lord", "name": "Menagerie Lord", "emoji": "🦖", "tier": "epic", "desc": "Own 100 animals.", "progress": lambda s: numeric_progress(s, "owned_animals_count", 100, "Animals")},
        {"id": "full_squad", "name": "Full Squad", "emoji": "🛡️", "tier": "rare", "desc": "Fill all 8 team slots.", "progress": lambda s: numeric_progress(s, "team_size", 8, "Team")},
        {"id": "alpha_pack", "name": "Alpha Pack", "emoji": "🐺", "tier": "epic", "desc": "Reach 1,000 total team power.", "progress": lambda s: numeric_progress(s, "team_power", 1_000, "Team Power")},
        {"id": "rare_bloodline", "name": "Rare Bloodline", "emoji": "🌌", "tier": "legendary", "desc": "Own 5 legendary-or-better animals.", "progress": lambda s: numeric_progress(s, "legendary_plus_animals", 5, "Legendary+")},
        {"id": "floorbreaker", "name": "Floorbreaker", "emoji": "🏰", "tier": "common", "desc": "Reach dungeon floor 5.", "progress": lambda s: numeric_progress(s, "dungeon_floor", 5, "Dungeon Floor")},
        {"id": "deep_delver", "name": "Deep Delver", "emoji": "🕳️", "tier": "rare", "desc": "Reach dungeon floor 25.", "progress": lambda s: numeric_progress(s, "dungeon_floor", 25, "Dungeon Floor")},
        {"id": "relic_gremlin", "name": "Relic Gremlin", "emoji": "🪬", "tier": "rare", "desc": "Hold 5 relics in a run.", "progress": lambda s: numeric_progress(s, "dungeon_relics", 5, "Relics")},
        {"id": "curse_carrier", "name": "Curse Carrier", "emoji": "☠️", "tier": "rare", "desc": "Carry 3 curses at once.", "progress": lambda s: numeric_progress(s, "dungeon_curses", 3, "Curses")},
        {"id": "raid_recruit", "name": "Raid Recruit", "emoji": "⚔️", "tier": "common", "desc": "Join a raid.", "progress": lambda s: (True, 100, "Joined a raid") if s.get("raid_joined") or s.get("raid_damage", 0) > 0 else (False, 0, "Join a raid")},
        {"id": "worldbreaker", "name": "Worldbreaker", "emoji": "💥", "tier": "epic", "desc": "Deal 10,000 raid damage.", "progress": lambda s: numeric_progress(s, "raid_damage", 10_000, "Raid Damage")},
        {"id": "arena_contender", "name": "Arena Contender", "emoji": "🏟️", "tier": "common", "desc": "Reach 1,200 arena rating.", "progress": lambda s: numeric_progress(s, "arena_rating", 1_200, "Arena Rating")},
        {"id": "crown_duelist", "name": "Crown Duelist", "emoji": "👑", "tier": "rare", "desc": "Reach 1,500 arena rating.", "progress": lambda s: numeric_progress(s, "arena_rating", 1_500, "Arena Rating")},
        {"id": "crown_hoarder", "name": "Crown Hoarder", "emoji": "🏆", "tier": "rare", "desc": "Collect 25 crowns.", "progress": lambda s: numeric_progress(s, "arena_crowns", 25, "Crowns")},
        {"id": "maze_touched", "name": "Maze-Touched", "emoji": "🌀", "tier": "common", "desc": "Reach Voidmaze depth 5.", "progress": lambda s: numeric_progress(s, "void_best_depth", 5, "Best Depth")},
        {"id": "abyss_walker", "name": "Abyss Walker", "emoji": "🌑", "tier": "epic", "desc": "Reach Voidmaze depth 25.", "progress": lambda s: numeric_progress(s, "void_best_depth", 25, "Best Depth")},
        {"id": "void_runner", "name": "Void Runner", "emoji": "🔮", "tier": "rare", "desc": "Reach a Voidmaze streak of 5.", "progress": lambda s: numeric_progress(s, "void_streak", 5, "Void Streak")},
        {"id": "lab_rat", "name": "Lab Rat", "emoji": "🧪", "tier": "common", "desc": "Reach lab level 5.", "progress": lambda s: numeric_progress(s, "lab_level", 5, "Lab Level")},
        {"id": "fracture_scholar", "name": "Fracture Scholar", "emoji": "🧬", "tier": "epic", "desc": "Unlock 3 lab breakthroughs.", "progress": lambda s: numeric_progress(s, "lab_breakthroughs", 3, "Breakthroughs")},
        {"id": "ghost_script", "name": "Ghost Script", "emoji": "🛠️", "tier": "common", "desc": "Reach hack skill 5.", "progress": lambda s: numeric_progress(s, "hack_skill", 5, "Hack Skill")},
        {"id": "ghost_operator", "name": "Ghost Operator", "emoji": "🕶️", "tier": "rare", "desc": "Reach 25 hack reputation.", "progress": lambda s: numeric_progress(s, "hack_reputation", 25, "Hack Rep")},
        {"id": "trace_spike", "name": "Trace Spike", "emoji": "📡", "tier": "rare", "desc": "Reach 50 trace.", "progress": lambda s: numeric_progress(s, "hack_trace", 50, "Trace")},
        {"id": "all_terrain", "name": "All-Terrain User", "emoji": "🧩", "tier": "legendary", "desc": "Be active in 6 different system groups.", "progress": lambda s: numeric_progress(s, "active_modes", 6, "Active Modes")},
        {"id": "all_rounder", "name": "All-Rounder", "emoji": "🌠", "tier": "legendary", "desc": "Reach grade B in all six masteries.", "progress": lambda s: _all_rounder_progress(s)},
        {"id": "horselord_prime", "name": "Horselord Prime", "emoji": "🐴", "tier": "mythic", "desc": "Hit six late-game milestones across the bot.", "progress": lambda s: _horselord_progress(s)},
    ]


def _all_rounder_progress(snapshot: dict):
    grades = system_scores(snapshot)
    count = sum(1 for value in grades.values() if value >= 55)
    percent = cap_percent((count / 6) * 100)
    return count >= 6, percent, f"B-or-better masteries: {count} / 6"


def _horselord_progress(snapshot: dict):
    checks = [
        snapshot["net_worth"] >= 250_000,
        snapshot["owned_animals_count"] >= 100,
        snapshot["void_best_depth"] >= 25,
        snapshot["arena_rating"] >= 1_500,
        snapshot["lab_level"] >= 10,
        snapshot["hack_skill"] >= 10,
    ]
    done = sum(1 for x in checks if x)
    percent = cap_percent((done / 6) * 100)
    return done >= 6, percent, f"Late-game milestones: {done} / 6"


def evaluate_achievements(snapshot: dict):
    results = []
    for definition in achievement_definitions():
        unlocked, percent, progress_text = definition["progress"](snapshot)
        points = TIER_POINTS[definition["tier"]] if unlocked else 0
        results.append({
            **definition,
            "unlocked": bool(unlocked),
            "percent": cap_percent(percent),
            "progress_text": progress_text,
            "points": points,
        })
    return results


def summarize_achievements(results: list[dict]):
    unlocked = [a for a in results if a["unlocked"]]
    total_points = sum(a["points"] for a in unlocked)
    tier_counts = {tier: 0 for tier in TIER_ORDER}
    for item in unlocked:
        tier_counts[item["tier"]] += 1
    completion = cap_percent((len(unlocked) / len(results)) * 100 if results else 0)
    return {
        "unlocked_count": len(unlocked),
        "total_count": len(results),
        "total_points": total_points,
        "tier_counts": tier_counts,
        "completion": completion,
    }


def mastery_grades(snapshot: dict):
    scores = system_scores(snapshot)
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"name": name, "score": round(score, 1), "grade": score_grade(score)} for name, score in ordered]


def choose_title(snapshot: dict, summary: dict, results: list[dict]) -> str:
    unlocked_ids = {a["id"] for a in results if a["unlocked"]}
    if "horselord_prime" in unlocked_ids:
        return "horselord prime"
    if "all_rounder" in unlocked_ids and "capital_engine" in unlocked_ids:
        return "fusion overlord"
    if "abyss_walker" in unlocked_ids:
        return "abyss sovereign"
    if "rare_bloodline" in unlocked_ids:
        return "beast king"
    if "worldbreaker" in unlocked_ids:
        return "raid tyrant"
    if "crown_duelist" in unlocked_ids:
        return "crown duelist"
    if "fracture_scholar" in unlocked_ids:
        return "fracture scholar"
    if "ghost_operator" in unlocked_ids:
        return "ghost operator"
    if "portfolio_player" in unlocked_ids:
        return "market climber"
    points = summary["total_points"]
    if points >= 160:
        return "server menace"
    if points >= 100:
        return "rift runner"
    if points >= 50:
        return "horsenncy hustler"
    if points >= 15:
        return "stable drifter"
    return "fresh spawn"


def next_up(results: list[dict], limit: int = 5):
    locked = [a for a in results if not a["unlocked"]]
    locked.sort(key=lambda a: (-a["percent"], TIER_ORDER.index(a["tier"]), a["name"]))
    return locked[:limit]


def rarest_unlocked(results: list[dict], limit: int = 5):
    unlocked = [a for a in results if a["unlocked"]]
    unlocked.sort(key=lambda a: (TIER_ORDER.index(a["tier"]), a["name"]))
    unlocked.reverse()
    return unlocked[:limit]


def get_profile_meta(user_id: int, data: dict | None = None):
    snapshot = build_snapshot(user_id, data)
    results = evaluate_achievements(snapshot)
    summary = summarize_achievements(results)
    title = choose_title(snapshot, summary, results)
    grades = mastery_grades(snapshot)
    return {
        "snapshot": snapshot,
        "results": results,
        "summary": summary,
        "title": title,
        "grades": grades,
        "next_up": next_up(results, limit=4),
        "rare_unlocked": rarest_unlocked(results, limit=4),
    }


def format_mastery_block(grades: list[dict], limit: int = 6) -> str:
    labels = {
        "economy": "Economy",
        "collection": "Collection",
        "combat": "Combat",
        "void": "Void",
        "research": "Research",
        "hack": "Hack",
    }
    lines = []
    for item in grades[:limit]:
        lines.append(f"{labels.get(item['name'], item['name'].title())}: `{item['grade']}`")
    return "\n".join(lines) if lines else "No mastery data yet"


def format_rare_unlocks(unlocks: list[dict]) -> str:
    if not unlocks:
        return "No rare unlocks yet"
    return "\n".join(f"{a['emoji']} **{a['name']}** — {TIER_LABELS[a['tier']]}" for a in unlocks)


def format_next_up(items: list[dict]) -> str:
    if not items:
        return "Everything unlocked"
    return "\n".join(f"{a['emoji']} **{a['name']}** — {a['progress_text']}" for a in items)


class Achievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="achievements", description="View FuSBot achievements for yourself or another user.")
    async def achievements(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        meta = get_profile_meta(target.id)
        snapshot = meta["snapshot"]
        summary = meta["summary"]
        grades = meta["grades"]
        results = meta["results"]

        embed = discord.Embed(
            title=f"🏆 {target.display_name}'s Achievements",
            description=(
                f"**Title:** `{meta['title']}`\n"
                f"**Unlocked:** `{summary['unlocked_count']}` / `{summary['total_count']}`\n"
                f"**Completion:** `{summary['completion']}%`\n"
                f"**Points:** `{summary['total_points']}`"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        wealth_text = f"`#{snapshot['wealth_rank']}` / `{snapshot['ranked_users']}`" if snapshot["wealth_rank"] else "`Unranked`"
        embed.add_field(
            name="Account Snapshot",
            value=(
                f"💎 **Net Worth:** `{snapshot['net_worth']:,}`\n"
                f"🏆 **Wealth Rank:** {wealth_text}\n"
                f"🎮 **Active Modes:** `{snapshot['active_modes']}`\n"
                f"⏱️ **Ready Cooldowns:** `{snapshot['ready_cooldowns']}` / `5`"
            ),
            inline=False
        )

        embed.add_field(name="Masteries", value=format_mastery_block(grades), inline=False)

        for tier in reversed(TIER_ORDER):
            unlocked = [a for a in results if a["unlocked"] and a["tier"] == tier]
            if not unlocked:
                continue
            text = "\n".join(f"{a['emoji']} {a['name']}" for a in unlocked)
            if len(text) > 1000:
                text = text[:997] + "..."
            embed.add_field(name=f"{TIER_EMOJIS[tier]} {TIER_LABELS[tier]}", value=text, inline=False)

        embed.add_field(name="Rare Unlocks", value=format_rare_unlocks(meta["rare_unlocked"]), inline=False)
        embed.add_field(name="Next Up", value=format_next_up(meta["next_up"]), inline=False)
        embed.set_footer(text="FuSBot achievements")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    print("Loading Achievements Cog...")
    await bot.add_cog(Achievements(bot))
    print("Achievements Cog Loaded!")
