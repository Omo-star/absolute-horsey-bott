import random
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from economy_shared import state, save_state
from economy import get_user, update_balance, get_pray_boost, get_balance


class VoidMaze(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="voidmaze", description="Enter the VOIDMAZE: a sanity-twisting choice roguelite.")
    async def voidmaze(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)

        vm = user.setdefault("voidmaze", {})
        vm.setdefault("active", False)
        vm.setdefault("depth", 0)
        vm.setdefault("clarity", 100)
        vm.setdefault("max_clarity", 100)
        vm.setdefault("keys", 0)
        vm.setdefault("artifacts", [])
        vm.setdefault("boons", [])
        vm.setdefault("anomalies", [])
        vm.setdefault("fragments", 0)
        vm.setdefault("runs", 0)
        vm.setdefault("streak", 0)
        vm.setdefault("last_log", "The Maze awakens and stares back.")
        vm.setdefault("best_depth", 0)
        vm.setdefault("synergy_cd", {})
        vm.setdefault("last_synergy_log", "")
        vm.setdefault("combo", 0)

        if vm["active"] is False:
            vm["depth"] = 0
            vm["clarity"] = vm["max_clarity"]
            vm["anomalies"] = []
            vm["boons"] = []
            vm["artifacts"] = []
            vm["keys"] = 0
            vm["fragments"] = 0
            vm["synergy_cd"] = {}
            vm["last_synergy_log"] = ""
            vm["combo"] = 0

        vm["active"] = True

        world = state.setdefault("voidmaze_world", {})
        world.setdefault("storm", 0.0)
        world.setdefault("pulse", 0.0)
        world.setdefault("season", 1)
        world.setdefault("last_event", "The labyrinth hums with cold awareness.")

        def power(v):
            base = v["depth"] * 6 + len(v["artifacts"]) * 10 + v["keys"] * 4 + v["fragments"] * 2
            base += v["streak"] * 8
            base += v.get("combo", 0) * 5
            penalty = len(v["anomalies"]) * 9
            return max(5, base - penalty)

        def clarity_mod(v):
            r = v["clarity"] / max(1, v["max_clarity"])
            if r >= 0.9:
                return 1.12, 0.01
            if r >= 0.7:
                return 1.0, 0.02
            if r >= 0.5:
                return 0.92, 0.03
            if r >= 0.3:
                return 0.85, 0.06
            return 0.75, 0.10

        def adjust_clarity(v, amt):
            v["clarity"] = max(0, min(v["max_clarity"], v["clarity"] + amt))
            if v["clarity"] == 0 and "Mind-Hollowed" not in v["anomalies"]:
                v["anomalies"].append("Mind-Hollowed")

        view = VoidmazeView(uid, vm, world, power, clarity_mod, adjust_clarity)
        await interaction.response.send_message(embed=view.render(), view=view)


class VoidmazeView(discord.ui.View):
    def __init__(self, uid, vm, world, power_fn, clarity_fn, adjust_clarity_fn):
        super().__init__(timeout=240)
        self.uid = uid
        self.vm = vm
        self.world = world
        self.power = power_fn
        self.clarity_mod = clarity_fn
        self.adjust_clarity = adjust_clarity_fn
        self.phase = 0
        self.current_rooms = self.generate_rooms()

    def render(self):
        pwr = self.power(self.vm)
        m, cpen = self.clarity_mod(self.vm)
        depth = self.vm["depth"]
        clarity = f"{self.vm['clarity']}/{self.vm['max_clarity']}"
        artifacts = len(self.vm["artifacts"])
        keys = self.vm["keys"]
        anomalies = len(self.vm["anomalies"])
        fragments = self.vm["fragments"]
        streak = self.vm["streak"]
        combo = self.vm.get("combo", 0)
        log = self.vm.get("last_log", "")
        synergy_log = self.vm.get("last_synergy_log", "")

        desc = ""
        for idx, room in enumerate(self.current_rooms, start=1):
            desc += f"**[{idx}] {room['name']}**\n{room['desc']}\n\n"

        embed = discord.Embed(
            title=f"🌀 VOIDMAZE — Depth {depth}",
            description=(
                desc
                + f"\n**Power:** {pwr}"
                + f"\n**Clarity:** {clarity}"
                + f"\n**Combo:** {combo}"
                + f"\n**Artifacts:** {artifacts}"
                + f"\n**Keys:** {keys}"
                + f"\n**Fragments:** {fragments}"
                + f"\n**Anomalies:** {anomalies}"
                + f"\n**Streak:** {streak}"
                + f"\n\n**{log}**"
            ),
            color=discord.Color.dark_purple()
        )

        embed.add_field(
            name="World State",
            value=(
                f"Storm {self.world['storm']:.2f} | "
                f"Pulse {self.world['pulse']:.2f} | "
                f"Season {self.world['season']}\n"
                f"{self.world['last_event']}"
            ),
            inline=False
        )

        if synergy_log:
            embed.add_field(
                name="Synergy Effects This Room",
                value=synergy_log,
                inline=False
            )

        return embed

    def generate_rooms(self):
        rooms = []
        choices = [
            self.room_abyss_door,
            self.room_key_node,
            self.room_artifact_vault,
            self.room_fracture,
            self.room_rest,
            self.room_echo_storm
        ]
        weights = [4, 3, 3, 3, 2, 1]
        pool = []

        for fn, w in zip(choices, weights):
            for _ in range(w):
                pool.append(fn)

        for _ in range(3):
            rooms.append(random.choice(pool)())

        return rooms

    async def update(self, inter, log_override=None):
        if log_override:
            self.vm["last_log"] = log_override
        await inter.response.edit_message(embed=self.render(), view=self)

    async def select_room(self, inter, index):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)

        if index < 1 or index > len(self.current_rooms):
            return await inter.response.send_message("Invalid room.", ephemeral=True)

        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended. Start a new run.", ephemeral=True)

        room = self.current_rooms[index - 1]
        await room["handler"](inter)

    @discord.ui.button(label="1", style=discord.ButtonStyle.primary)
    async def btn_1(self, inter: discord.Interaction, btn: discord.ui.Button):
        await self.select_room(inter, 1)

    @discord.ui.button(label="2", style=discord.ButtonStyle.primary)
    async def btn_2(self, inter: discord.Interaction, btn: discord.ui.Button):
        await self.select_room(inter, 2)

    @discord.ui.button(label="3", style=discord.ButtonStyle.primary)
    async def btn_3(self, inter: discord.Interaction, btn: discord.ui.Button):
        await self.select_room(inter, 3)

    @discord.ui.button(label="Leave Maze", style=discord.ButtonStyle.red)
    async def btn_leave(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)

        final_depth = self.vm["depth"]
        combo = self.vm.get("combo", 0)

        reward = int(
            final_depth * 45
            + len(self.vm["artifacts"]) * 140
            + self.vm["keys"] * 25
            + self.vm["fragments"] * 18
            - len(self.vm["anomalies"]) * 60
            + self.world["storm"] * 30
            + combo * 20
        )

        reward = max(0, reward)
        await update_balance(self.uid, reward)

        self.vm["best_depth"] = max(self.vm["best_depth"], final_depth)

        self.vm["active"] = False
        self.vm["runs"] += 1
        self.vm["streak"] += 1

        self.vm["depth"] = 0
        self.vm["clarity"] = self.vm["max_clarity"]
        self.vm["anomalies"] = []
        self.vm["boons"] = []
        self.vm["artifacts"] = []
        self.vm["keys"] = 0
        self.vm["fragments"] = 0
        self.vm["synergy_cd"] = {}
        self.vm["last_synergy_log"] = ""
        self.vm["combo"] = 0

        self.vm["last_log"] = f"You escape the Maze with {reward} horsenncy."
        save_state()

        await inter.response.edit_message(
            embed=discord.Embed(
                title="🌀 VOIDMAZE — Run Complete",
                description=(
                    f"You reached depth **{final_depth}**.\n"
                    f"Combo streak: **{combo}**.\n"
                    f"Reward: **{reward} horsenncy**."
                ),
                color=discord.Color.green()
            ),
            view=None
        )

    def room_abyss_door(self):
        return {
            "name": "Door of the Abyss",
            "desc": "A humming monolith leaking black light. Power rises, clarity bleeds.",
            "handler": self.handle_abyss_door
        }

    def room_key_node(self):
        return {
            "name": "Tangle Key Node",
            "desc": "Threads of logic and illusion knot together. Solving it grants a Maze Key.",
            "handler": self.handle_key_node
        }

    def room_artifact_vault(self):
        return {
            "name": "Artifact Vault",
            "desc": "A floating vault of mirrors. Contains an Artifact or something far worse.",
            "handler": self.handle_artifact_vault
        }

    def room_fracture(self):
        return {
            "name": "Reality Fracture",
            "desc": "A raw tear into impossible geometry. Immense rewards or instant collapse.",
            "handler": self.handle_fracture
        }

    def room_rest(self):
        return {
            "name": "Locus of Stillness",
            "desc": "A calm white chamber where the Maze forgets to breathe. Clarity may return.",
            "handler": self.handle_rest
        }

    def room_echo_storm(self):
        return {
            "name": "Echo Storm",
            "desc": "The Maze convulses with cosmic thunder. Global effects ripple outward.",
            "handler": self.handle_echo_storm
        }

    async def handle_abyss_door(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        pwr = self.power(self.vm)
        m, cpen = self.clarity_mod(self.vm)

        gain_frag = int(2 + self.vm["depth"] * 0.4 + pwr * 0.05)
        clarity_loss = random.randint(5, 14)

        self.vm["depth"] += 1
        self.vm["fragments"] += gain_frag
        self.vm["combo"] = self.vm.get("combo", 0) + 1
        self.adjust_clarity(self.vm, -clarity_loss)

        if random.random() < cpen:
            anomaly = random.choice(["Hollow Static", "Worming Echo", "Loose Geometry"])
            self.vm["anomalies"].append(anomaly)
            self.vm["combo"] = 0
            log = f"The door floods you with power but twists you. Gain {gain_frag} fragments and anomaly {anomaly}."
        else:
            log = f"The door pulses. Gain {gain_frag} fragments but lose {clarity_loss} clarity. Combo grows."

        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    async def handle_key_node(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        puzzle = random.choice(["left", "right", "center"])
        choice = random.choice(["left", "right", "center"])

        success = puzzle == choice
        clarity_shift = random.randint(-4, 8)

        if success:
            self.vm["keys"] += 1
            self.vm["depth"] += 1
            self.vm["combo"] = self.vm.get("combo", 0) + 1
            self.adjust_clarity(self.vm, clarity_shift)
            if random.random() < 0.25:
                boon = self.roll_boon_reward()
                log = f"Your intuition aligns with the Maze. Gain 1 key, {clarity_shift} clarity, and boon {boon}."
            else:
                log = f"Your intuition aligns with the Maze. Gain 1 key and {clarity_shift} clarity."
        else:
            self.adjust_clarity(self.vm, -abs(clarity_shift))
            anomaly = random.choice(["Fractured Insight", "Recursive Loop"])
            self.vm["anomalies"].append(anomaly)
            self.vm["combo"] = 0
            log = f"The Node rejects you. You gain anomaly {anomaly} and lose clarity."

        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    async def handle_artifact_vault(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        tier = 1 + self.vm["depth"] // 5
        tier = min(tier, 5)

        artifact_tables = {
            1: ["Glass Feather", "Silent Pebble", "Hollow Ring"],
            2: ["Inverse Lantern", "Fractal Glyph", "Reversed Compass"],
            3: ["Abyssal Crown", "Cubic Heart", "Orb of Warp"],
            4: ["Star-Bleed Idol", "Ghost Spiral", "Temporal Harness"],
            5: ["Omega Prism", "Eternal Coil", "Riftborn Crown"]
        }

        artifact = random.choice(artifact_tables[tier])

        bad_roll = random.random() < 0.25
        clarity_hit = random.randint(3, 12)

        self.vm["artifacts"].append(artifact)
        self.vm["depth"] += 1

        if bad_roll:
            anomaly = random.choice(["Artifact Backlash", "Mirror Shatter"])
            self.vm["anomalies"].append(anomaly)
            self.vm["combo"] = 0
            self.adjust_clarity(self.vm, -clarity_hit)
            log = (
                f"The vault yields {artifact}, but backlash inflicts "
                f"{anomaly} and {clarity_hit} clarity loss."
            )
        else:
            heal = random.randint(1, 7)
            self.adjust_clarity(self.vm, heal)
            self.vm["combo"] = self.vm.get("combo", 0) + 1
            if random.random() < 0.35:
                boon = self.roll_boon_reward()
                log = f"The vault gifts you {artifact} and boon {boon}. The Maze hums approvingly."
            else:
                log = f"The vault gifts you {artifact}. The Maze hums approvingly."

        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    async def handle_fracture(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        roll = random.random()
        pwr = self.power(self.vm)

        if roll < 0.25:
            drop = int(170 + pwr * 0.9 + self.vm["depth"] * 4)
            await update_balance(self.uid, drop)
            self.vm["depth"] += 2
            self.vm["fragments"] += 4
            self.vm["combo"] = self.vm.get("combo", 0) + 2
            self.adjust_clarity(self.vm, -random.randint(5, 15))
            log = f"The fracture erupts with wealth. Gain {drop} horsenncy and surge deeper."
        elif roll < 0.55:
            art = random.choice(["Echo Crown", "Warp Tablet", "Obsidian Bloom"])
            self.vm["artifacts"].append(art)
            self.vm["depth"] += 1
            self.vm["combo"] = self.vm.get("combo", 0) + 1
            self.adjust_clarity(self.vm, -random.randint(4, 8))
            if random.random() < 0.3:
                boon = self.roll_boon_reward()
                log = f"The fracture gifts artifact {art} and boon {boon}, but clarity bleeds."
            else:
                log = f"The fracture gifts artifact {art}, but clarity bleeds."
        elif roll < 0.85:
            anomaly = random.choice(["Time Shear", "Phase Drift", "Soul Split"])
            self.vm["anomalies"].append(anomaly)
            self.vm["depth"] += 1
            self.vm["combo"] = 0
            self.adjust_clarity(self.vm, -random.randint(10, 20))
            log = f"The fracture lashes out. You gain anomaly {anomaly}."
        else:
            self.vm["active"] = False
            penalty = int(pwr * 1.5 + self.vm["depth"] * 20)
            penalty = min(penalty, await get_balance(self.uid))
            await update_balance(self.uid, -penalty)
            save_state()
            return await inter.response.edit_message(
                embed=discord.Embed(
                    title="💀 VOIDMAZE — Collapse",
                    description=f"The fracture consumes you. You lose {penalty} horsenncy.",
                    color=discord.Color.red()
                ),
                view=None
            )

        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    async def handle_rest(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        danger = 0.25 + self.world["storm"] * 0.1

        if random.random() < danger:
            dmg = random.randint(6, 16)
            self.adjust_clarity(self.vm, -dmg)
            anomaly = random.choice(["Parasitic Dream", "Mind Static"])
            self.vm["anomalies"].append(anomaly)
            self.vm["combo"] = 0
            log = f"Rest is shattered by a whisper. Lose {dmg} clarity and gain anomaly {anomaly}."
        else:
            heal = random.randint(10, 25)
            self.adjust_clarity(self.vm, heal)
            self.vm["depth"] += 1
            self.vm["combo"] = 0
            if random.random() < 0.2:
                boon = self.roll_boon_reward()
                log = f"Stillness restores you. Regain {heal} clarity and receive boon {boon}."
            else:
                log = f"Stillness restores you. Regain {heal} clarity."

        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    async def handle_echo_storm(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Maze.", ephemeral=True)
        if not self.vm["active"]:
            return await inter.response.send_message("This Maze run has ended.", ephemeral=True)

        r = random.random()

        if r < 0.33:
            self.world["storm"] += 0.4
            self.world["pulse"] += 0.1
            self.vm["depth"] += 1
            self.vm["combo"] = self.vm.get("combo", 0) + 1
            self.adjust_clarity(self.vm, -random.randint(6, 12))
            log = "The Maze convulses. Storm intensifies and you are dragged deeper."
        elif r < 0.66:
            self.world["pulse"] += 0.3
            reward = int(70 + self.vm["depth"] * 6)
            await update_balance(self.uid, reward)
            self.vm["fragments"] += 3
            if random.random() < 0.3:
                boon = self.roll_boon_reward()
                log = f"The pulse grants {reward} horsenncy, fragments, and boon {boon}."
            else:
                log = f"The pulse grants {reward} horsenncy and fragments."
        else:
            self.world["season"] += 1
            self.world["storm"] *= 0.5
            self.world["pulse"] *= 0.3
            self.vm["depth"] += 2
            self.vm["combo"] = self.vm.get("combo", 0) + 2
            self.adjust_clarity(self.vm, random.randint(4, 12))
            log = "A season turns. The Maze shifts and you slip further in, strangely refreshed."

        self.world["last_event"] = log
        self.vm["last_log"] = log
        self.current_rooms = self.generate_rooms()
        await self.after_room(inter)

    def _roll_cooldown(self, key):
        ranges = {
            "glass_pebble": (2, 4),
            "abyss_lantern": (2, 4),
            "omega_prism": (1, 3),
            "ghost_spiral": (3, 6),
            "echo_recursive": (2, 4),
            "warp_phase": (3, 5),
            "temporal_shear": (2, 4),
            "fractal_glyph": (3, 6),
            "reversed_compass": (1, 3),
            "cubic_worm": (2, 5),
            "eternal_coil": (1, 4),
            "star_bleed": (3, 7),
            "obsidian_bloom": (2, 4),
            "hollow_static": (1, 2),
            "loose_geometry": (2, 4),
            "parasitic_dream": (1, 2),
            "mind_static": (2, 5),
            "recursion_blessing": (2, 4),
            "stillheart_boon": (1, 3),
            "stormwalker_boon": (3, 6),
            "glyphreader_insight": (2, 4),
            "pulse_harmony": (2, 5)
        }

        lo, hi = ranges.get(key, (2, 4))
        return random.randint(lo, hi)

    def apply_synergies(self):
        arts = self.vm["artifacts"]
        anoms = self.vm["anomalies"]
        boons = self.vm.get("boons", [])
        sy_cd = self.vm.setdefault("synergy_cd", {})

        lines = []

        def can_trigger(key):
            cd = sy_cd.get(key, 0)
            if cd > 0:
                sy_cd[key] = cd - 1
                return False
            return True

        def trigger(key, text, effect_fn):
            if not can_trigger(key):
                return
            effect_fn()
            sy_cd[key] = self._roll_cooldown(key)
            lines.append(text)

        if "Glass Feather" in arts and "Silent Pebble" in arts:
            trigger(
                "glass_pebble",
                "Glass Feather + Silent Pebble → Clarity +2",
                lambda: self.adjust_clarity(self.vm, 2)
            )

        if "Abyssal Crown" in arts and "Inverse Lantern" in arts:
            def f_abyss_lantern():
                self.world["storm"] += 0.02
            trigger(
                "abyss_lantern",
                "Abyssal Crown + Inverse Lantern → Storm +0.02",
                f_abyss_lantern
            )

        if "Omega Prism" in arts:
            trigger(
                "omega_prism",
                "Omega Prism → Fragments +1",
                lambda: self.vm.__setitem__("fragments", self.vm["fragments"] + 1)
            )

        if "Ghost Spiral" in arts and self.world["pulse"] > 0.3:
            trigger(
                "ghost_spiral",
                "Ghost Spiral (Pulse > 0.3) → Depth +1",
                lambda: self.vm.__setitem__("depth", self.vm["depth"] + 1)
            )

        if "Echo Crown" in arts and "Recursive Loop" in anoms:
            def f_echo_recursive():
                self.adjust_clarity(self.vm, -3)
                self.vm["fragments"] += 2
            trigger(
                "echo_recursive",
                "Echo Crown + Recursive Loop → Clarity -3, Fragments +2",
                f_echo_recursive
            )

        if "Warp Tablet" in arts and "Phase Drift" in anoms:
            trigger(
                "warp_phase",
                "Warp Tablet + Phase Drift → Keys +1",
                lambda: self.vm.__setitem__("keys", self.vm["keys"] + 1)
            )

        if "Temporal Harness" in arts and "Time Shear" in anoms:
            trigger(
                "temporal_shear",
                "Temporal Harness + Time Shear → Depth +1",
                lambda: self.vm.__setitem__("depth", self.vm["depth"] + 1)
            )

        if "Fractal Glyph" in arts:
            trigger(
                "fractal_glyph",
                "Fractal Glyph → Depth +1",
                lambda: self.vm.__setitem__("depth", self.vm["depth"] + 1)
            )

        if "Reversed Compass" in arts:
            def f_reversed_compass():
                if random.random() < 0.15:
                    self.vm["depth"] += 1
            trigger(
                "reversed_compass",
                "Reversed Compass → 15% chance Depth +1",
                f_reversed_compass
            )

        if "Cubic Heart" in arts and "Worming Echo" in anoms:
            trigger(
                "cubic_worm",
                "Cubic Heart + Worming Echo → Clarity -2",
                lambda: self.adjust_clarity(self.vm, -2)
            )

        if "Eternal Coil" in arts:
            def f_eternal_coil():
                self.world["pulse"] += 0.01
            trigger(
                "eternal_coil",
                "Eternal Coil → Pulse +0.01",
                f_eternal_coil
            )

        if "Star-Bleed Idol" in arts and self.vm["clarity"] < 40:
            trigger(
                "star_bleed",
                "Star-Bleed Idol (Low Clarity) → Fragments +4",
                lambda: self.vm.__setitem__("fragments", self.vm["fragments"] + 4)
            )

        if "Obsidian Bloom" in arts:
            def f_obsidian_bloom():
                if random.random() < 0.2:
                    self.vm["fragments"] += 3
            trigger(
                "obsidian_bloom",
                "Obsidian Bloom → 20% chance Fragments +3",
                f_obsidian_bloom
            )

        if "Hollow Static" in anoms:
            trigger(
                "hollow_static",
                "Hollow Static → Clarity -1",
                lambda: self.adjust_clarity(self.vm, -1)
            )

        if "Loose Geometry" in anoms:
            def f_loose_geometry():
                if random.random() < 0.1:
                    self.vm["depth"] += 1
            trigger(
                "loose_geometry",
                "Loose Geometry → 10% chance Depth +1",
                f_loose_geometry
            )

        if "Parasitic Dream" in anoms:
            def f_parasitic_dream():
                self.vm["clarity"] = max(1, self.vm["clarity"] - 1)
            trigger(
                "parasitic_dream",
                "Parasitic Dream → Clarity -1",
                f_parasitic_dream
            )

        if "Mind Static" in anoms:
            def f_mind_static():
                if random.random() < 0.1 and self.vm["keys"] > 0:
                    self.vm["keys"] -= 1
            trigger(
                "mind_static",
                "Mind Static → 10% chance lose 1 Key",
                f_mind_static
            )

        if "Recursion Blessing" in boons:
            def f_recursion():
                if random.random() < 0.15:
                    self.vm["fragments"] += 2
            trigger(
                "recursion_blessing",
                "Recursion Blessing → 15% chance Fragments +2",
                f_recursion
            )

        if "Stillheart Boon" in boons:
            def f_stillheart():
                if self.vm["clarity"] < self.vm["max_clarity"]:
                    self.adjust_clarity(self.vm, 1)
            trigger(
                "stillheart_boon",
                "Stillheart Boon → Clarity +1 (if not full)",
                f_stillheart
            )

        if "Stormwalker Boon" in boons:
            def f_stormwalker():
                if self.world["storm"] > 0.5:
                    self.vm["depth"] += 1
            trigger(
                "stormwalker_boon",
                "Stormwalker Boon (High Storm) → Depth +1",
                f_stormwalker
            )

        if "Glyphreader Insight" in boons:
            def f_glyphreader():
                if random.random() < 0.25:
                    self.vm["fragments"] += 1
                    self.adjust_clarity(self.vm, 1)
            trigger(
                "glyphreader_insight",
                "Glyphreader Insight → 25% chance Fragments +1 and Clarity +1",
                f_glyphreader
            )

        if "Pulse Harmony" in boons:
            def f_pulse_harmony():
                if self.world["pulse"] > 0.5:
                    self.vm["depth"] += 1
                    self.adjust_clarity(self.vm, 1)
            trigger(
                "pulse_harmony",
                "Pulse Harmony (High Pulse) → Depth +1 and Clarity +1",
                f_pulse_harmony
            )

        if lines:
            self.vm["last_synergy_log"] = "\n".join(f"• {line}" for line in lines)
        else:
            self.vm["last_synergy_log"] = ""

    def roll_boon_reward(self, forced=None):
        if forced is not None:
            self.vm.setdefault("boons", [])
            self.vm["boons"].append(forced)
            return forced
        boons = [
            "Recursion Blessing",
            "Stillheart Boon",
            "Stormwalker Boon",
            "Glyphreader Insight",
            "Pulse Harmony"
        ]
        boon = random.choice(boons)
        self.vm.setdefault("boons", [])
        self.vm["boons"].append(boon)
        return boon

    def apply_passive_world_effects(self):
        if self.world["storm"] > 1.5:
            self.world["pulse"] += 0.02
        if self.world["pulse"] > 1.0:
            self.world["season"] += 1
            self.world["pulse"] *= 0.4
            self.world["storm"] *= 0.6
            self.world["last_event"] = "The Maze enters a new micro-season."
        if self.world["storm"] < 0:
            self.world["storm"] = 0
        if self.world["pulse"] < 0:
            self.world["pulse"] = 0

    async def after_room(self, inter):
        self.apply_synergies()
        self.apply_passive_world_effects()
        save_state()
        await self.update(inter)


async def setup(bot):
    await bot.add_cog(VoidMaze(bot))
