import discord
import random
import asyncio
import datetime
from discord.ext import commands
from discord import app_commands

from economy import get_user, save_state, state, update_balance, get_balance, get_pray_boost


class ResearchLab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lab", description="Enter the Horsey Research Laboratory.")
    async def lab(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)

        lab = user.setdefault("lab", {})
        lab.setdefault("level", 1)
        lab.setdefault("xp", 0)
        lab.setdefault("stability", 100)
        lab.setdefault("max_stability", 100)
        lab.setdefault("anomalies", [])
        lab.setdefault("breakthroughs", [])
        lab.setdefault("queue", [])
        lab.setdefault("running", False)
        lab.setdefault("last_log", "The machinery hums as you enter.")

        world = state.setdefault("lab_world", {})
        world.setdefault("instability", 0.0)
        world.setdefault("discoveries", 0)
        world.setdefault("last_event", "The labs are unusually calm.")

        view = LabView(uid, lab, world)
        await interaction.response.send_message(embed=view.render_main(), view=view)
class LabView(discord.ui.View):
    def __init__(self, uid, lab, world):
        super().__init__(timeout=240)
        self.uid = uid
        self.lab = lab
        self.world = world
        self.phase = 0

    def render_main(self):
        lvl = self.lab["level"]
        xp = self.lab["xp"]
        stab = self.lab["stability"]
        max_stab = self.lab["max_stability"]
        anomalies = len(self.lab["anomalies"])
        bts = len(self.lab["breakthroughs"])
        log = self.lab["last_log"]

        wmsg = (
            f"Instability {self.world['instability']:.2f}\n"
            f"{self.world['last_event']}"
        )

        embed = discord.Embed(
            title="🧪 HORSEY RESEARCH LAB",
            description=(
                f"**Level:** {lvl}\n"
                f"**XP:** {xp}\n"
                f"**Stability:** {stab}/{max_stab}\n"
                f"**Anomalies:** {anomalies}\n"
                f"**Breakthroughs:** {bts}\n\n"
                f"**{log}**"
            ),
            color=discord.Color.teal()
        )

        embed.add_field(
            name="Lab World",
            value=wmsg,
            inline=False
        )

        return embed

    async def refresh(self, inter):
        await inter.response.edit_message(embed=self.render_main(), view=self)

    @discord.ui.button(label="Research", style=discord.ButtonStyle.green)
    async def btn_research(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)
        await self.begin_research(inter)

    @discord.ui.button(label="Experiment", style=discord.ButtonStyle.blurple)
    async def btn_experiment(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)
        await self.run_experiment(inter)

    @discord.ui.button(label="Stabilize", style=discord.ButtonStyle.secondary)
    async def btn_stabilize(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)
        await self.perform_stabilization(inter)

    @discord.ui.button(label="Breakthroughs", style=discord.ButtonStyle.primary)
    async def btn_break(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)
        await self.show_breakthroughs(inter)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red)
    async def btn_leave(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)
        await inter.response.edit_message(
            embed=discord.Embed(
                title="🧪 Lab Closed",
                description="You step away from the humming machines.",
                color=discord.Color.dark_red()
            ),
            view=None
        )

    async def begin_research(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)

        fields = ["Economy", "Dungeonology", "Arena Theory", "Cosmic Luck"]
        field = random.choice(fields)

        base_xp = random.randint(18, 35)
        instability_gain = random.uniform(0.03, 0.09)
        stab_loss = random.randint(2, 7)

        self.lab["xp"] += base_xp
        self.lab["stability"] = max(0, self.lab["stability"] - stab_loss)
        self.world["instability"] += instability_gain

        leveled = False
        while self.lab["xp"] >= 100:
            self.lab["xp"] -= 100
            self.lab["level"] += 1
            self.world["discoveries"] += 1
            leveled = True

        bt_log = ""
        bt_chance = 0.06 + self.lab["level"] * 0.01 + self.world["instability"] * 0.02

        if random.random() < bt_chance:
            table = [
                "Efficient Stock Algos",
                "Dungeon Resonance Mapping",
                "Arena Combat Analytics",
                "Prayer Wave Amplifier",
                "Casino Edge Tuning",
                "Meta-Currency Compression"
            ]
            bt = random.choice(table)
            if bt not in self.lab["breakthroughs"]:
                self.lab["breakthroughs"].append(bt)
                bt_log = f" Breakthrough unlocked: **{bt}**."
            else:
                self.lab["xp"] += 20

        log = (
            f"Researched **{field}** for {base_xp} XP, "
            f"stability -{stab_loss}, instability +{instability_gain:.2f}."
        )

        if leveled:
            log += f" Lab leveled up to {self.lab['level']}."
        if bt_log:
            log += " " + bt_log

        if self.lab["stability"] <= 0:
            self.lab["stability"] = 0
            if "Core Fracture" not in self.lab["anomalies"]:
                self.lab["anomalies"].append("Core Fracture")
            log += " The core fractures under pressure."

        self.lab["last_log"] = log
        self.world["last_event"] = "A surge of research energy ripples across all labs."

        save_state()
        await self.refresh(inter)

    async def run_experiment(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)

        balance = await get_balance(self.uid)
        if balance < 80:
            return await inter.response.send_message("You lack enough horsenncy to fund an experiment.", ephemeral=True)

        stake = max(80, min(balance // 10, 600))
        await update_balance(self.uid, -stake)

        r = random.random()
        pray_boost = get_pray_boost(self.uid)

        if r < 0.22:
            mult = random.uniform(1.4, 2.6)
            gain = int(stake * mult * pray_boost)
            await update_balance(self.uid, gain)
            xp_gain = random.randint(10, 25)
            self.lab["xp"] += xp_gain
            self.lab["stability"] = max(0, self.lab["stability"] - random.randint(4, 10))
            self.world["instability"] += 0.10
            log = (
                f"Experiment yields a lucrative result. You gain {gain} horsenncy "
                f"and {xp_gain} lab XP."
            )
        elif r < 0.60:
            mult = random.uniform(0.8, 1.3)
            gain = int(stake * mult)
            await update_balance(self.uid, gain)
            self.lab["stability"] = max(0, self.lab["stability"] - random.randint(2, 6))
            self.world["instability"] += 0.04
            log = (
                f"The experiment is mildly successful. Net result: "
                f"{gain - stake:+} horsenncy."
            )
        elif r < 0.88:
            loss = int(stake * random.uniform(0.4, 1.2))
            loss = min(loss, await get_balance(self.uid))
            await update_balance(self.uid, -loss)
            self.lab["stability"] = max(0, self.lab["stability"] - random.randint(5, 12))
            self.world["instability"] += 0.08
            anomaly = random.choice(["Phantom Feedback", "Quantum Noise", "Harmonic Glitch"])
            self.lab["anomalies"].append(anomaly)
            log = (
                f"The experiment misbehaves. Extra loss {loss} horsenncy and anomaly "
                f"{anomaly} appears."
            )
        else:
            extra_loss = min(int(stake * 2), await get_balance(self.uid))
            await update_balance(self.uid, -extra_loss)
            stab_crash = random.randint(15, 35)
            self.lab["stability"] = max(0, self.lab["stability"] - stab_crash)
            self.world["instability"] += 0.18
            anomaly = random.choice(["Lab Explosion", "Temporal Backdraft", "Spatial Tear"])
            self.lab["anomalies"].append(anomaly)
            log = (
                f"Catastrophic failure. You lose an extra {extra_loss} horsenncy, "
                f"stability -{stab_crash}, anomaly {anomaly} forms."
            )

        if self.lab["stability"] <= 0 and "Core Fracture" not in self.lab["anomalies"]:
            self.lab["anomalies"].append("Core Fracture")
            self.lab["stability"] = 0
            log += " The fractured core screams silently."

        self.lab["last_log"] = log
        self.world["last_event"] = "Experimental waves distort the lab complex."

        save_state()
        await self.refresh(inter)

    async def perform_stabilization(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)

        if self.lab["stability"] >= self.lab["max_stability"]:
            self.lab["last_log"] = "Systems already at peak stability."
            save_state()
            return await self.refresh(inter)

        cost_xp = random.randint(8, 18)
        heal = random.randint(12, 28)
        world_reduce = random.uniform(0.05, 0.18)

        if self.lab["xp"] < cost_xp:
            return await inter.response.send_message("Not enough lab XP to run a stabilization cycle.", ephemeral=True)

        self.lab["xp"] -= cost_xp
        self.lab["stability"] = min(self.lab["max_stability"], self.lab["stability"] + heal)
        self.world["instability"] = max(0.0, self.world["instability"] - world_reduce)

        removed = None
        if self.lab["anomalies"] and random.random() < 0.35:
            removed = random.choice(self.lab["anomalies"])
            self.lab["anomalies"].remove(removed)

        log = (
            f"Stabilization cycle engaged. Stability +{heal}, "
            f"instability -{world_reduce:.2f}."
        )

        if removed:
            log += f" Anomaly {removed} is neutralized."

        self.lab["last_log"] = log
        self.world["last_event"] = "A stabilizing wave passes through the lab network."

        save_state()
        await self.refresh(inter)

    async def show_breakthroughs(self, inter):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your lab.", ephemeral=True)

        bt = self.lab["breakthroughs"]
        if not bt:
            text = "No breakthroughs discovered yet."
        else:
            desc_map = {
                "Efficient Stock Algos": "Minor edge on market-related features and simulations.",
                "Dungeon Resonance Mapping": "Understanding of dungeon rifts improves flavor and future synergies.",
                "Arena Combat Analytics": "Deep statistics for Arena battles, enabling stronger builds.",
                "Prayer Wave Amplifier": "Theoretical boost to global prayer phenomena.",
                "Casino Edge Tuning": "Insights into gambling behaviors and odds manipulation.",
                "Meta-Currency Compression": "Research into densifying value flows across all systems."
            }
            lines = []
            for name in bt:
                d = desc_map.get(name, "Mysterious effect not yet understood.")
                lines.append(f"• **{name}** — {d}")
            text = "\n".join(lines)

        embed = discord.Embed(
            title="🔬 Lab Breakthroughs",
            description=text,
            color=discord.Color.teal()
        )

        v = discord.ui.View(timeout=180)

        async def back_callback(bi):
            if bi.user.id != self.uid:
                return await bi.response.send_message("Not your lab.", ephemeral=True)
            await bi.response.edit_message(embed=self.render_main(), view=self)

        back_btn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = back_callback
        v.add_item(back_btn)

        await inter.response.edit_message(embed=embed, view=v)

async def setup(bot):
    await bot.add_cog(ResearchLab(bot))
