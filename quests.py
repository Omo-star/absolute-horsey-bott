import datetime
import random
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user
from economy_shared import state, save_state

try:
    from achievement import build_snapshot
except Exception:
    build_snapshot = None


class QuestBoard:
    QUEST_POOL = [
        {"id": "balance_1k", "label": "Hold 1,000 horsenncy", "key": "balance", "goal": 1000, "reward": 250},
        {"id": "balance_10k", "label": "Hold 10,000 horsenncy", "key": "balance", "goal": 10000, "reward": 900},
        {"id": "net_25k", "label": "Reach 25,000 net worth", "key": "net_worth", "goal": 25000, "reward": 1250},
        {"id": "pray_10", "label": "Reach 10 prayer points", "key": "pray_points", "goal": 10, "reward": 220},
        {"id": "inv_10", "label": "Own 10 unique inventory items", "key": "inventory_unique", "goal": 10, "reward": 300},
        {"id": "animals_10", "label": "Own 10 animals", "key": "owned_animals_count", "goal": 10, "reward": 420},
        {"id": "team_500", "label": "Reach 500 team power", "key": "team_power", "goal": 500, "reward": 650},
        {"id": "stocks_5k", "label": "Reach 5,000 portfolio value", "key": "stock_value", "goal": 5000, "reward": 500},
        {"id": "dungeon_5", "label": "Reach dungeon floor 5", "key": "dungeon_floor", "goal": 5, "reward": 500},
        {"id": "raid_1k", "label": "Deal 1,000 raid damage", "key": "raid_damage", "goal": 1000, "reward": 700},
        {"id": "arena_1200", "label": "Reach 1,200 arena rating", "key": "arena_rating", "goal": 1200, "reward": 800},
        {"id": "void_5", "label": "Reach Voidmaze depth 5", "key": "void_best_depth", "goal": 5, "reward": 650},
        {"id": "lab_5", "label": "Reach lab level 5", "key": "lab_level", "goal": 5, "reward": 650},
        {"id": "hack_5", "label": "Reach hack skill 5", "key": "hack_skill", "goal": 5, "reward": 650},
        {"id": "active_5", "label": "Be active in 5 system groups", "key": "active_modes", "goal": 5, "reward": 1200},
    ]

    @staticmethod
    def today_key():
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

    @staticmethod
    def snapshot_for(uid: int):
        if build_snapshot:
            return build_snapshot(uid)
        data = get_user(uid)
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
        stock_value = 0
        return {
            "balance": int(data.get("balance", 0) or 0),
            "net_worth": int(data.get("balance", 0) or 0) + stock_value,
            "pray_points": int(data.get("pray", 0) or 0),
            "inventory_unique": sum(1 for qty in inventory.values() if int(qty or 0) > 0),
            "owned_animals_count": len(owned_animals),
            "team_power": team_power,
            "stock_value": stock_value,
            "dungeon_floor": int(dungeon.get("floor", 1) or 1),
            "raid_damage": int(raid.get("damage", 0) or 0),
            "arena_rating": int(arena.get("rating", 0) or 0),
            "void_best_depth": int(voidmaze.get("best_depth", 0) or 0),
            "lab_level": int(lab.get("level", 0) or 0),
            "hack_skill": int(hack.get("skill", 0) or 0),
            "active_modes": sum(1 for x in [bool(inventory), bool(owned_animals), bool(team), bool(arena), bool(voidmaze), bool(lab), bool(hack)] if x),
        }

    @staticmethod
    def state_root():
        return state.setdefault("quest_progress_v1", {})

    @classmethod
    def user_state(cls, uid: int):
        root = cls.state_root()
        key = str(uid)
        today = cls.today_key()
        if key not in root or root[key].get("day") != today:
            rng = random.Random(f"{uid}:{today}:fusquests")
            picks = rng.sample(cls.QUEST_POOL, k=min(3, len(cls.QUEST_POOL)))
            root[key] = {
                "day": today,
                "quest_ids": [q["id"] for q in picks],
                "claimed": [],
            }
            save_state()
        return root[key]

    @classmethod
    def board_for(cls, uid: int):
        user_state = cls.user_state(uid)
        lookup = {q["id"]: q for q in cls.QUEST_POOL}
        snapshot = cls.snapshot_for(uid)
        board = []
        for idx, quest_id in enumerate(user_state.get("quest_ids", []), start=1):
            q = lookup.get(quest_id)
            if not q:
                continue
            current = int(snapshot.get(q["key"], 0) or 0)
            done = current >= q["goal"]
            claimed = quest_id in user_state.get("claimed", [])
            pct = min(100, int(round((current / q["goal"]) * 100))) if q["goal"] > 0 else 100
            board.append({
                "index": idx,
                "id": quest_id,
                "label": q["label"],
                "current": current,
                "goal": q["goal"],
                "reward": q["reward"],
                "done": done,
                "claimed": claimed,
                "percent": pct,
            })
        return board

    @classmethod
    def claim(cls, uid: int, index: int):
        board = cls.board_for(uid)
        if index < 1 or index > len(board):
            return False, "that quest slot doesnt exist"
        quest = board[index - 1]
        if quest["claimed"]:
            return False, "that quest is already claimed"
        if not quest["done"]:
            return False, "you havent finished that quest yet"
        user_state = cls.user_state(uid)
        user_state.setdefault("claimed", []).append(quest["id"])
        data = get_user(uid)
        data["balance"] = int(data.get("balance", 0) or 0) + quest["reward"]
        save_state()
        return True, quest


class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="quests", description="View your daily quest board.")
    async def quests(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        board = QuestBoard.board_for(target.id)
        today = QuestBoard.today_key()
        complete_count = sum(1 for q in board if q["done"])
        claimed_count = sum(1 for q in board if q["claimed"])

        embed = discord.Embed(
            title=f"📜 {target.display_name}'s Daily Quests",
            description=f"day `{today}` • completed `{complete_count}` / `{len(board)}` • claimed `{claimed_count}` / `{len(board)}`",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        if not board:
            embed.add_field(name="Board", value="no quests rolled", inline=False)
        else:
            lines = []
            for quest in board:
                status = "✅ claimed" if quest["claimed"] else "🟢 done" if quest["done"] else "🟡 in progress"
                lines.append(
                    f"`{quest['index']}` **{quest['label']}**\n"
                    f"{status} • `{quest['current']}` / `{quest['goal']}` • reward `{quest['reward']}`"
                )
            embed.add_field(name="Quest Board", value="\n\n".join(lines), inline=False)

        embed.set_footer(text="use /quests_claim <slot> to claim a finished quest")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quests_claim", description="Claim a finished daily quest by slot number.")
    @app_commands.describe(slot="Quest number from /quests")
    async def quests_claim(self, interaction: discord.Interaction, slot: app_commands.Range[int, 1, 3]):
        ok, result = QuestBoard.claim(interaction.user.id, int(slot))
        if not ok:
            await interaction.response.send_message(result, ephemeral=True)
            return

        embed = discord.Embed(
            title="🎉 quest claimed",
            description=(
                f"**{result['label']}**\n"
                f"reward: `{result['reward']}` horsenncy"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    print("Loading Quests Cog...")
    await bot.add_cog(Quests(bot))
    print("Quests Cog Loaded!")
