import random
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user, save_state, state, update_balance, get_balance, get_pray_boost


class HorseyArena(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="arena", description="Enter the Horsey Arena auto-battler.")
    async def arena(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)

        arena = user.setdefault("arena", {})
        arena.setdefault("rating", 1000)
        arena.setdefault("tokens", 3)
        arena.setdefault("crowns", 0)
        arena.setdefault("wins", 0)
        arena.setdefault("losses", 0)
        arena.setdefault("streak", 0)
        arena.setdefault("level", 1)
        arena.setdefault("xp", 0)
        arena.setdefault("last_log", "The Arena gate creaks open.")
        arena.setdefault("in_battle", False)
        arena.setdefault("loadout", [])
        arena.setdefault("last_opponent", None)

        owned = user.setdefault("owned_animals", [])
        team = user.setdefault("team", [])

        world = state.setdefault("arena_world", {})
        world.setdefault("season", 1)
        world.setdefault("chaos", 0.0)
        world.setdefault("total_matches", 0)
        world.setdefault("last_champion", None)
        world.setdefault("last_event", "The sands are quiet.")
        world.setdefault("ladder", {})

        if not arena["loadout"]:
            arena["loadout"] = list(team[:5])

        view = ArenaView(
            uid=uid,
            arena=arena,
            world=world,
            owned_animals=owned,
            team_ref=team
        )

        await interaction.response.send_message(embed=view.render_lobby(), view=view)
class ArenaView(discord.ui.View):
    def __init__(self, uid, arena, world, owned_animals, team_ref):
        super().__init__(timeout=240)
        self.uid = uid
        self.arena = arena
        self.world = world
        self.owned = owned_animals
        self.team = team_ref
        self.phase = 0
    def pet_name(self, pet):
        if isinstance(pet, dict):
            return pet.get("name", "Unknown")
        return str(pet)
    def render_lobby(self):
        rating = self.arena["rating"]
        tokens = self.arena["tokens"]
        crowns = self.arena["crowns"]
        wins = self.arena["wins"]
        losses = self.arena["losses"]
        streak = self.arena["streak"]
        level = self.arena["level"]
        xp = self.arena["xp"]
        loadout = self.arena["loadout"]
        log = self.arena["last_log"]

        world_msg = (
            f"Season {self.world['season']} | "
            f"Chaos {self.world['chaos']:.2f}\n"
            f"{self.world['last_event']}"
        )

        team_text = "None" if not loadout else ", ".join(
            self.pet_name(pet) for pet in loadout
        )

        embed = discord.Embed(
            title="🏟️ HORSEY ARENA — LOBBY",
            description=(
                f"**Rating:** {rating}\n"
                f"**Tokens:** {tokens}\n"
                f"**Crowns:** {crowns}\n"
                f"**Wins:** {wins} | **Losses:** {losses} | **Streak:** {streak}\n"
                f"**Level:** {level} ({xp} XP)\n\n"
                f"**Team Loadout:** {team_text}\n\n"
                f"**{log}**"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Arena World",
            value=world_msg,
            inline=False
        )

        return embed

    async def refresh(self, inter):
        await inter.response.edit_message(embed=self.render_lobby(), view=self)

    @discord.ui.button(label="Fight Match", style=discord.ButtonStyle.green)
    async def btn_fight(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)

        if self.arena["tokens"] <= 0:
            return await inter.response.send_message("You have no fight tokens left.", ephemeral=True)

        await self.start_match(inter)

    @discord.ui.button(label="Edit Team", style=discord.ButtonStyle.blurple)
    async def btn_edit(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)

        await self.edit_team(inter)

    @discord.ui.button(label="View Ladder", style=discord.ButtonStyle.secondary)
    async def btn_ladder(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)

        await self.show_ladder(inter)

    @discord.ui.button(label="Leave Arena", style=discord.ButtonStyle.red)
    async def btn_leave(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)

        await inter.response.edit_message(
            embed=discord.Embed(
                title="🏟️ Arena Closed",
                description="You step away from the sands.",
                color=discord.Color.dark_red()
            ),
            view=None
        )
    async def start_match(self, inter):
        self.arena["tokens"] -= 1
        self.arena["in_battle"] = True

        player_team = list(self.arena["loadout"])
        if not player_team:
            return await inter.response.send_message("You have no team selected.", ephemeral=True)

        opp = self.generate_opponent()

        pstats = self.build_team_stats(player_team)
        ostats = self.build_team_stats(opp)

        result, battle_log = self.simulate_battle(pstats, ostats)

        await self.process_match_result(inter, result, battle_log, opp)

    def generate_opponent(self):
        size = random.randint(3, 5)
        pool = ["Horse", "Cow", "Goat", "Chicken", "Pig", "Donkey", "Sheep", "Ox", "Bull", "Yak"]
        team = [random.choice(pool) for _ in range(size)]
        self.arena["last_opponent"] = team
        return team

    def build_team_stats(self, team):
        stats = []
        passives = self.arena.setdefault("passives", {})
        power_mult = 1.0 + passives.get("power_boost", 0.0)
        speed_mult = 1.0 + passives.get("speed_boost", 0.0)
        def_mult = 1.0 + passives.get("def_boost", 0.0)
        crit_bonus = passives.get("crit_boost", 0.0)

        chaos_factor = 1.0 + self.world["chaos"] * 0.2

        for unit in team:
            name = unit["name"] if isinstance(unit, dict) else str(unit)
            base_power = random.randint(40, 90)
            base_speed = random.randint(20, 60)
            base_def = random.randint(10, 40)
            crit = random.uniform(0.05, 0.15) + crit_bonus

            base_power = int(base_power * chaos_factor * power_mult)
            base_speed = int(base_speed * speed_mult)
            base_def = int(base_def * def_mult)

            if crit > 0.6:
                crit = 0.6
            if crit < 0.01:
                crit = 0.01

            stats.append({
                "name": name,
                "hp": base_power * 2,
                "power": base_power,
                "speed": base_speed,
                "def": base_def,
                "crit": crit
            })

        return stats


    def simulate_battle(self, pstats, ostats):
        log = []
        turn = 1

        while True:
            turn += 1

            attacker_side = random.choice(["player", "opp"])

            if attacker_side == "player":
                attacker = random.choice(pstats)
                defender = random.choice(ostats)
            else:
                attacker = random.choice(ostats)
                defender = random.choice(pstats)

            if attacker["hp"] <= 0 or defender["hp"] <= 0:
                continue

            dmg = attacker["power"] - defender["def"]
            if dmg < 5:
                dmg = 5

            if random.random() < attacker["crit"]:
                dmg = int(dmg * 1.7)
                crit_txt = " (CRIT!)"
            else:
                crit_txt = ""

            defender["hp"] -= dmg
            log.append(f"{self.pet_name(attacker)} hits {self.pet_name(defender)} for {dmg}{crit_txt}")

            p_alive = sum(1 for u in pstats if u["hp"] > 0)
            o_alive = sum(1 for u in ostats if u["hp"] > 0)

            if p_alive == 0:
                return "loss", log
            if o_alive == 0:
                return "win", log

            if turn > 200:
                return "draw", log

    async def process_match_result(self, inter, result, battle_log, opp):
        rating = self.arena["rating"]
        xp = self.arena["xp"]
        level = self.arena["level"]
        streak = self.arena["streak"]

        if result == "win":
            delta = random.randint(14, 28)
            xp_gain = random.randint(20, 40)
            crowns = random.randint(0, 1)
            rating += delta
            xp += xp_gain
            streak += 1
            self.arena["wins"] += 1
            self.arena["crowns"] += crowns
            self.world["chaos"] += 0.02
            result_txt = (
                f"Victory!\nRating +{delta}\nXP +{xp_gain}\nCrowns +{crowns}"
            )

        elif result == "loss":
            delta = -random.randint(8, 20)
            xp_gain = random.randint(10, 22)
            rating += delta
            xp += xp_gain
            streak = 0
            self.arena["losses"] += 1
            self.world["chaos"] += 0.01
            result_txt = (
                f"Defeat.\nRating {delta}\nXP +{xp_gain}"
            )

        else:
            xp_gain = random.randint(5, 12)
            xp += xp_gain
            result_txt = f"Draw.\nXP +{xp_gain}"

        while xp >= 100:
            xp -= 100
            level += 1
            self.arena["crowns"] += 1
            self.world["chaos"] += 0.05

        self.arena["rating"] = max(0, rating)
        self.arena["xp"] = xp
        self.arena["level"] = level
        self.arena["streak"] = streak
        self.arena["last_log"] = result_txt
        self.world["total_matches"] += 1

        if self.world["chaos"] > 5:
            self.world["season"] += 1
            self.world["chaos"] = 0
            self.world["last_event"] = "A new Arena Season begins!"

        save_state()

        battle_text = "\n".join(battle_log[-20:])
        opp_text = ", ".join(self.pet_name(o) for o in opp)

        embed = discord.Embed(
            title="🏟️ ARENA MATCH RESULT",
            description=(
                f"**Result:** {result.upper()}\n"
                f"**Opponent Team:** {opp_text}\n\n"
                f"**{self.arena['last_log']}**\n\n"
                f"**Battle Log (Last 20 events):**\n{battle_text}"
            ),
            color=discord.Color.gold()
        )

        await inter.response.edit_message(embed=embed, view=self)
    async def edit_team(self, inter):
        if not self.owned:
            return await inter.response.send_message("You own no animals.", ephemeral=True)

        options = []
        for name in self.owned:
            options.append(discord.SelectOption(label=name, value=name))

        select = discord.ui.Select(
            placeholder="Select up to 5 animals for your Arena team",
            min_values=1,
            max_values=min(5, len(options)),
            options=options
        )

        async def select_callback(sel_inter):
            if sel_inter.user.id != self.uid:
                return await sel_inter.response.send_message("Not your Arena.", ephemeral=True)
            self.arena["loadout"] = list(select.values)
            self.arena["last_log"] = f"Team updated: {', '.join(select.values)}"
            save_state()
            await sel_inter.response.edit_message(embed=self.render_lobby(), view=self)

        select.callback = select_callback

        v = discord.ui.View(timeout=180)
        v.add_item(select)

        await inter.response.edit_message(
            embed=discord.Embed(
                title="Edit Arena Team",
                description="Select which animals you want in your battle team.",
                color=discord.Color.blurple()
            ),
            view=v
        )

    async def show_ladder(self, inter):
        ladder = self.world.setdefault("ladder", {})
        uid = str(self.uid)
        ladder[uid] = self.arena["rating"]

        sorted_pairs = sorted(ladder.items(), key=lambda x: x[1], reverse=True)
        top = sorted_pairs[:10]

        lines = []
        for i, (pid, rating) in enumerate(top, 1):
            try:
                user_obj = await inter.client.fetch_user(int(pid))
                name = user_obj.display_name
            except:
                name = f"User {pid}"
            lines.append(f"**#{i}** {name} — {rating}")

        board = "\n".join(lines) if lines else "No ranked players yet."

        embed = discord.Embed(
            title="🏆 Arena Ladder",
            description=board,
            color=discord.Color.gold()
        )

        v = discord.ui.View(timeout=120)

        async def back_callback(bi):
            if bi.user.id != self.uid:
                return await bi.response.send_message("Not your Arena.", ephemeral=True)
            await bi.response.edit_message(embed=self.render_lobby(), view=self)

        back_btn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = back_callback
        v.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=v)

    async def crown_shop(self, inter):
        items = {
            "might": {
                "name": "Might Emblem",
                "cost": 3,
                "key": "power_boost",
                "amount": 0.05
            },
            "haste": {
                "name": "Haste Emblem",
                "cost": 3,
                "key": "speed_boost",
                "amount": 0.07
            },
            "ward": {
                "name": "Ward Emblem",
                "cost": 3,
                "key": "def_boost",
                "amount": 0.07
            },
            "luck": {
                "name": "Lucky Emblem",
                "cost": 4,
                "key": "crit_boost",
                "amount": 0.03
            }
        }

        options = []
        for key, data in items.items():
            options.append(
                discord.SelectOption(
                    label=data["name"],
                    value=key,
                    description=f"Cost {data['cost']} crowns"
                )
            )

        select = discord.ui.Select(
            placeholder="Spend crowns on permanent Arena buffs",
            min_values=1,
            max_values=1,
            options=options
        )

        async def select_callback(sel_inter):
            if sel_inter.user.id != self.uid:
                return await sel_inter.response.send_message("Not your Arena.", ephemeral=True)

            choice = select.values[0]
            data = items[choice]
            cost = data["cost"]

            if self.arena["crowns"] < cost:
                return await sel_inter.response.send_message("Not enough crowns for that purchase.", ephemeral=True)

            self.arena["crowns"] -= cost
            passives = self.arena.setdefault("passives", {})
            key = data["key"]
            amount = data["amount"]
            passives[key] = passives.get(key, 0.0) + amount
            self.arena["last_log"] = f"Purchased {data['name']}."

            save_state()
            await sel_inter.response.edit_message(embed=self.render_lobby(), view=self)

        select.callback = select_callback

        v = discord.ui.View(timeout=180)
        v.add_item(select)

        embed = discord.Embed(
            title="🎖️ Arena Crown Shop",
            description=(
                f"You have {self.arena['crowns']} crowns.\n"
                f"Choose a permanent Arena buff to purchase."
            ),
            color=discord.Color.orange()
        )

        async def back_callback(bi):
            if bi.user.id != self.uid:
                return await bi.response.send_message("Not your Arena.", ephemeral=True)
            await bi.response.edit_message(embed=self.render_lobby(), view=self)

        back_btn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = back_callback
        v.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=v)

    @discord.ui.button(label="Crown Shop", style=discord.ButtonStyle.secondary)
    async def btn_shop(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        await self.crown_shop(inter)



async def setup(bot):
    await bot.add_cog(HorseyArena(bot))
