import random
import discord
from discord.ext import commands
from discord import app_commands
from economy_shared import state, save_state
from economy import get_user, update_balance, get_balance, get_pray_boost


class Dungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dungeon", description="Enter the evolving dungeon: rifts, sanity, raids, invasions, and world bosses.")
    async def dungeon(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)
        global state

        world = state.setdefault("world", {})
        world.setdefault("corruption", 0.0)
        world.setdefault("raid_seed", random.randint(1, 999999))
        world.setdefault("raid_boss", None)
        world.setdefault("raid_hp", 0)
        world.setdefault("raid_max_hp", 0)
        world.setdefault("raid_cycle", 0)
        world.setdefault("last_event", "Dormant")
        world.setdefault("rift_level", 0)
        world.setdefault("rift_instability", 0.0)

        dungeon = user.setdefault("dungeon", {})
        dungeon.setdefault("active", False)
        dungeon.setdefault("floor", 1)
        dungeon.setdefault("hp", 100)
        dungeon.setdefault("max_hp", 100)
        dungeon.setdefault("energy", 5)
        dungeon.setdefault("skills", {"might": 0, "ward": 0, "greed": 0, "warp": 0, "instinct": 0})
        dungeon.setdefault("relics", [])
        dungeon.setdefault("curses", [])
        dungeon.setdefault("mutations", [])
        dungeon.setdefault("afflictions", [])
        dungeon.setdefault("skill_points", 0)
        dungeon.setdefault("last_floor_cleared", 0)
        dungeon.setdefault("raid_tokens", 1)
        dungeon.setdefault("invasion_shield", 0)
        dungeon.setdefault("last_log", "You feel the dungeon watching you.")
        dungeon.setdefault("runs", 0)
        dungeon.setdefault("boss_kills", 0)
        dungeon.setdefault("sanity", 100)
        dungeon.setdefault("max_sanity", 100)
        dungeon.setdefault("rift_depth", 0)

        if not dungeon["active"]:
            dungeon["floor"] = 1
            dungeon["hp"] = dungeon["max_hp"]
            dungeon["energy"] = 5
            dungeon["sanity"] = dungeon["max_sanity"]
            dungeon["rift_depth"] = 0
            dungeon["relics"] = []
            dungeon["curses"] = []
            dungeon["mutations"] = []
            dungeon["afflictions"] = []
            dungeon["invasion_shield"] = 0
            dungeon["last_log"] = "You descend into a fresh rifted dungeon."

        dungeon["active"] = True
        session_id = random.randint(1, 10**12)
        dungeon["session_id"] = session_id
        save_state()

        def get_power(d):
            s = d["skills"]
            base = d["floor"] * 12 + len(d["relics"]) * 9
            base += s["might"] * 14
            base += s["ward"] * 5
            base += s["instinct"] * 8
            base += d["rift_depth"] * 3
            base += len(d["mutations"]) * 6
            penalty = len(d["curses"]) * 11 + len(d["afflictions"]) * 8
            return max(10, base - penalty)

        def get_luck(d):
            s = d["skills"]
            base = 1.0 + s["greed"] * 0.09 + len(d["relics"]) * 0.02
            base += len(d["mutations"]) * 0.01
            base -= len(d["curses"]) * 0.04
            base -= d["rift_depth"] * 0.005
            return max(0.15, base)

        def get_warp(d):
            s = d["skills"]
            value = s["warp"] * 0.035 + len(d["relics"]) * 0.006
            value += d["rift_depth"] * 0.004
            return value

        def get_sanity_modifier(d):
            san = max(0, min(d["sanity"], d["max_sanity"]))
            ratio = san / max(1, d["max_sanity"])
            if ratio >= 0.9:
                return 1.05, 0.0
            if ratio >= 0.7:
                return 1.0, 0.0
            if ratio >= 0.5:
                return 0.95, 0.02
            if ratio >= 0.3:
                return 0.9, 0.05
            return 0.82, 0.1

        def get_rift_pressure(d):
            return 0.05 + d["rift_depth"] * 0.01 + world["rift_instability"] * 0.15

        def adjust_sanity(d, delta):
            d["sanity"] = max(0, min(d["max_sanity"], d["sanity"] + delta))
            if d["sanity"] == 0 and "Broken Mind" not in d["curses"]:
                d["curses"].append("Broken Mind")

        def ensure_raid_boss():
            if world["raid_boss"] is None or world["raid_hp"] <= 0:
                world["raid_cycle"] += 1
                names = [
                    "Abyssal World-Serpent",
                    "Chronophage Colossus",
                    "Starlit Void Leviathan",
                    "Omega Horsey of Endings",
                    "Reality-Flaying Dragon"
                ]
                boss = random.choice(names)
                base_hp = 1200 + int(world["corruption"] * 350) + world["raid_cycle"] * 320
                base_hp += world["rift_level"] * 120
                world["raid_boss"] = boss
                world["raid_hp"] = base_hp
                world["raid_max_hp"] = base_hp
                world["last_event"] = f"New raid boss: {boss}"
                save_state()

        def dungeon_summary(d):
            s = d["skills"]
            hp_bar = f"{d['hp']}/{d['max_hp']}"
            energy_bar = f"{d['energy']} ⚡"
            sanity_bar = f"{d['sanity']}/{d['max_sanity']}"
            relics = len(d["relics"])
            curses = len(d["curses"])
            muts = len(d["mutations"])
            power = get_power(d)
            luck = get_luck(d)
            warp = get_warp(d)
            return (
                f"Floor: {d['floor']}\n"
                f"HP: {hp_bar} | Sanity: {sanity_bar}\n"
                f"Energy: {energy_bar}\n"
                f"Relics: {relics} | Curses: {curses} | Mutations: {muts}\n"
                f"Power: {power} | Luck: {luck:.2f} | Warp: {warp:.2f}\n"
                f"Skills → Might {s['might']}, Ward {s['ward']}, Greed {s['greed']}, Warp {s['warp']}, Instinct {s['instinct']}\n"
                f"Skill Points: {d['skill_points']} | Raid Tokens: {d['raid_tokens']}\n"
                f"Rift Depth: {d['rift_depth']} | World Corruption: {world['corruption']:.2f} | Rift Level: {world['rift_level']}\n"
                f"World Event: {world['last_event']}"
            )

        def pick_invasion_target(exclude_id):
            candidates = []
            for raw_id, udata in state["users"].items():
                try:
                    tid = int(raw_id)
                except:
                    continue
                if tid == exclude_id:
                    continue
                d2 = udata.get("dungeon")
                if not d2:
                    continue
                if not d2.get("active"):
                    continue
                if d2.get("hp", 0) <= 0:
                    continue
                candidates.append((tid, d2))
            if not candidates:
                return None
            return random.choice(candidates)

        class DungeonView(discord.ui.View):
            def __init__(self, dungeon_state, session_id):
                super().__init__(timeout=240)
                self.d = dungeon_state
                self.session_id = session_id
                self.title = f"🌌 Dungeon Rift — {interaction.user.display_name}"

            def is_stale(self):
                if not self.d.get("active"):
                    return True
                if self.d.get("session_id") != self.session_id:
                    return True
                return False

            def build_embed(self):
                desc = dungeon_summary(self.d) + "\n\n" + self.d.get("last_log", "")
                e = discord.Embed(
                    title=self.title,
                    description=desc,
                    color=discord.Color.dark_purple()
                )
                if world["raid_boss"]:
                    hp = world["raid_hp"]
                    max_hp = max(1, world["raid_max_hp"])
                    ratio = max(0.0, min(1.0, hp / max_hp))
                    blocks = 14
                    filled = int(blocks * ratio)
                    bar = "█" * filled + "░" * (blocks - filled)
                    e.add_field(
                        name=f"Global Raid Boss: {world['raid_boss']}",
                        value=f"{bar}\nHP: {hp}/{max_hp}",
                        inline=False
                    )
                return e

            async def refresh_message(self, inter):
                if self.is_stale():
                    await inter.response.edit_message(
                        embed=discord.Embed(
                            title=self.title,
                            description="This dungeon run has ended. Use /dungeon to start a new run.",
                            color=discord.Color.dark_grey()
                        ),
                        view=None
                    )
                    return
                await inter.response.edit_message(embed=self.build_embed(), view=self)

            async def do_explore(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                if self.d["hp"] <= 0:
                    self.d["active"] = False
                    save_state()
                    await inter.response.edit_message(
                        embed=discord.Embed(
                            title=self.title,
                            description="You cannot move. The dungeon has consumed you.",
                            color=discord.Color.dark_red()
                        ),
                        view=None
                    )
                    return
                if self.d["energy"] <= 0:
                    self.d["last_log"] = "You are exhausted. Rest, or dive into a rift at your own risk."
                    save_state()
                    await self.refresh_message(inter)
                    return
                self.d["energy"] -= 1
                world["corruption"] += 0.02 + self.d["floor"] * 0.001
                san_mult, extra_curse = get_sanity_modifier(self.d)
                pressure = get_rift_pressure(self.d)
                event_roll = random.random()
                boss_floor = self.d["floor"] % 7 == 0
                if boss_floor and random.random() < 0.6 * san_mult:
                    await self.handle_boss(inter)
                    return
                if event_roll < 0.32:
                    await self.handle_battle(inter, san_mult, extra_curse)
                elif event_roll < 0.54:
                    await self.handle_loot(inter, san_mult)
                elif event_roll < 0.70:
                    await self.handle_trap(inter, san_mult, extra_curse)
                elif event_roll < 0.82:
                    await self.handle_altar(inter)
                elif event_roll < 0.92:
                    await self.handle_world_rift(inter, pressure)
                else:
                    invasion_chance = 0.08 + get_warp(self.d) * 0.5 + pressure * 0.4
                    if random.random() < invasion_chance and self.d["invasion_shield"] <= 0:
                        await self.handle_invasion(inter)
                    else:
                        await self.handle_world_rift(inter, pressure)

            async def handle_battle(self, inter, san_mult, extra_curse):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                power = get_power(self.d) * san_mult
                luck = get_luck(self.d)
                ward = self.d["skills"]["ward"]
                tier = min(6, 1 + self.d["floor"] // 5)
                monsters = {
                    1: [("Gloom Slime", 40, 0.70), ("Duskwolf", 65, 0.62)],
                    2: [("Abyss Stalker", 120, 0.55), ("Shatter Imp", 150, 0.50)],
                    3: [("Grave Titan", 240, 0.44), ("Spectral Butcher", 260, 0.42)],
                    4: [("Entropy Hydra", 360, 0.36), ("Obsidian Warden", 380, 0.34)],
                    5: [("World Scar", 520, 0.30), ("Chrono Horror", 560, 0.28)],
                    6: [("Rift-Torn Colossus", 700, 0.26), ("Mind-Latched Leviathan", 740, 0.24)]
                }
                name, reward, base_win = random.choice(monsters[tier])
                win_chance = base_win + power * 0.0008 + luck * 0.02 - world["corruption"] * 0.01
                win_chance -= world["rift_instability"] * 0.02
                win_chance = max(0.05, min(0.96, win_chance))
                if random.random() < win_chance:
                    crit = random.random() < (0.08 + self.d["skills"]["might"] * 0.02)
                    final_reward = int(reward * luck * (2 if crit else 1))
                    pray_mult = get_pray_boost(uid)
                    final_reward = int(final_reward * pray_mult)
                    await update_balance(uid, final_reward)
                    self.d["floor"] += 1
                    self.d["last_floor_cleared"] = max(self.d["last_floor_cleared"], self.d["floor"])
                    if self.d["floor"] % 4 == 0:
                        self.d["skill_points"] += 1
                    adjust_sanity(self.d, random.randint(0, 3))
                    text = f"You defeated {name} and gained {final_reward} horsenncy."
                    if crit:
                        text += " Critical strike shreds the echo of reality."
                    self.d["last_log"] = text
                else:
                    dmg = random.randint(18, 60) + int(world["corruption"] * 5)
                    dmg = max(1, int(dmg * (1 - ward * 0.06)))
                    dmg = int(dmg * (1.0 + world["rift_instability"] * 0.4))
                    self.d["hp"] -= dmg
                    adjust_sanity(self.d, -random.randint(3, 8))
                    if extra_curse > 0 and random.random() < extra_curse:
                        curse = random.choice(["Shivering Mind", "Fading Color", "Static Whispers"])
                        self.d["curses"].append(curse)
                    if self.d["hp"] <= 0:
                        self.d["hp"] = 0
                        self.d["active"] = False
                        save_state()
                        await inter.response.edit_message(
                            embed=discord.Embed(
                                title=self.title,
                                description=f"{name} crushed you.\nYou lost consciousness at floor {self.d['floor']}.",
                                color=discord.Color.dark_red()
                            ),
                            view=None
                        )
                        return
                    self.d["last_log"] = f"{name} wounded you for {dmg} HP. Your head rings."
                save_state()
                await self.refresh_message(inter)

            async def handle_loot(self, inter, san_mult):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                luck = get_luck(self.d)
                base = random.randint(50, 200) + self.d["floor"] * 15
                coin = int(base * luck * san_mult)
                pray_mult = get_pray_boost(uid)
                coin = int(coin * pray_mult)
                relic_roll = random.random() < 0.20 + luck * 0.05
                curse_roll = random.random() < 0.04 + world["corruption"] * 0.02
                mut_roll = random.random() < 0.06 + self.d["rift_depth"] * 0.01
                await update_balance(uid, coin)
                log = f"You find a warped cache worth {coin} horsenncy."
                if relic_roll:
                    relic_pool = [
                        "Temporal Shard",
                        "Crown of Echoes",
                        "Void Mane Fragment",
                        "Prismatic Hoofprint",
                        "Stellar Bridle",
                        "Gilded Neighstone",
                        "Riftglass Eye"
                    ]
                    relic = random.choice(relic_pool)
                    self.d["relics"].append(relic)
                    log += f" You obtained relic: {relic}."
                if mut_roll:
                    mut_pool = ["Extra Spine", "Glass Nerves", "Echoing Hoof", "Fractal Tail"]
                    mut = random.choice(mut_pool)
                    self.d["mutations"].append(mut)
                    adjust_sanity(self.d, -random.randint(2, 5))
                    log += f" A rift brands you with mutation: {mut}."
                if curse_roll:
                    curses = ["Mark of Hunger", "Fractured Time", "Weak Hoof", "Gaze of the Abyss"]
                    curse = random.choice(curses)
                    self.d["curses"].append(curse)
                    log += f" A lurking curse clings to you: {curse}."
                self.d["floor"] += 1
                if self.d["floor"] % 4 == 0:
                    self.d["skill_points"] += 1
                self.d["last_log"] = log
                save_state()
                await self.refresh_message(inter)

            async def handle_trap(self, inter, san_mult, extra_curse):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                ward = self.d["skills"]["ward"]
                dmg = random.randint(25, 130) + int(world["corruption"] * 10)
                dmg = max(5, int(dmg * (1 - ward * 0.05)))
                dmg = int(dmg * (1.0 + world["rift_instability"] * 0.4))
                evade = 0.10 + self.d["skills"]["instinct"] * 0.03
                if random.random() < evade * san_mult:
                    self.d["last_log"] = "You sense a layered trap and narrowly dodge it."
                else:
                    self.d["hp"] -= dmg
                    adjust_sanity(self.d, -random.randint(5, 12))
                    if extra_curse > 0 and random.random() < extra_curse + 0.05:
                        curse = random.choice(["Hollow Pulse", "Bleeding Colors", "Rusting Soul"])
                        self.d["curses"].append(curse)
                    if self.d["hp"] <= 0:
                        self.d["hp"] = 0
                        self.d["active"] = False
                        save_state()
                        await inter.response.edit_message(
                            embed=discord.Embed(
                                title=self.title,
                                description=f"A catastrophic trap obliterates you on floor {self.d['floor']}.",
                                color=discord.Color.dark_red()
                            ),
                            view=None
                        )
                        return
                    self.d["last_log"] = f"A trap tears through you for {dmg} HP. Reality snaps in your ears."
                self.d["floor"] += 1
                save_state()
                await self.refresh_message(inter)

            async def handle_altar(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                roll = random.random()
                if roll < 0.40:
                    heal = random.randint(20, 80) + self.d["skills"]["ward"] * 10
                    self.d["hp"] = min(self.d["max_hp"], self.d["hp"] + heal)
                    adjust_sanity(self.d, random.randint(4, 9))
                    self.d["last_log"] = f"A radiant altar mends your wounds for {heal} HP and soothes your thoughts."
                elif roll < 0.70:
                    self.d["skill_points"] += 1
                    adjust_sanity(self.d, random.randint(1, 4))
                    self.d["last_log"] = "You receive an echo of knowledge. Gain 1 skill point."
                else:
                    curses = ["Silent Brand", "Bone Tax", "Entropy Mark"]
                    curse = random.choice(curses)
                    self.d["curses"].append(curse)
                    adjust_sanity(self.d, -random.randint(4, 10))
                    self.d["last_log"] = f"A false altar curses you with {curse}."
                self.d["floor"] += 1
                save_state()
                await self.refresh_message(inter)

            async def handle_world_rift(self, inter, pressure):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                ensure_raid_boss()
                warp = get_warp(self.d)
                roll = random.random()
                if roll < 0.23 + warp:
                    world["corruption"] = max(0.0, world["corruption"] - 0.30)
                    world["rift_instability"] = max(0.0, world["rift_instability"] - 0.08)
                    world["last_event"] = "A cleansing wave sweeps the dungeon."
                    adjust_sanity(self.d, random.randint(5, 12))
                    self.d["last_log"] = "You witness a cleansing rift that lowers world corruption and calms your mind."
                elif roll < 0.50 + pressure:
                    world["corruption"] += 0.5
                    world["rift_instability"] += 0.10
                    world["rift_level"] += 1
                    world["last_event"] = "A catastrophic surge mutates the raid boss and deepens all rifts."
                    if world["raid_boss"]:
                        world["raid_hp"] = int(world["raid_hp"] * 1.20) + 120
                        world["raid_max_hp"] = int(world["raid_max_hp"] * 1.20) + 120
                    adjust_sanity(self.d, -random.randint(5, 14))
                    self.d["last_log"] = "A violent rift swells the global boss and drags at your thoughts."
                else:
                    shift = random.choice(["up", "down"])
                    if shift == "up":
                        self.d["floor"] += 2
                        self.d["rift_depth"] += 1
                        adjust_sanity(self.d, -random.randint(2, 6))
                        self.d["last_log"] = "A twisted rift hurls you two floors upward and deeper into its echo."
                    else:
                        self.d["floor"] = max(1, self.d["floor"] - 2)
                        self.d["rift_depth"] = max(0, self.d["rift_depth"] - 1)
                        adjust_sanity(self.d, random.randint(1, 5))
                        self.d["last_log"] = "A collapsing rift drags you two floors downward, releasing some pressure."
                self.d["floor"] += 1
                save_state()
                await self.refresh_message(inter)

            async def handle_boss(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                power = get_power(self.d)
                luck = get_luck(self.d)
                boss_names = [
                    "Crown-Eater Stallion",
                    "Oblivion Roc",
                    "Sunless Unicorn King",
                    "Titanic Leviathan Colt",
                    "Rift-Crowned Archbeast"
                ]
                hp_scale = 80 + self.d["floor"] * 25 + int(world["corruption"] * 40) + int(world["rift_instability"] * 120)
                boss_name = random.choice(boss_names)
                win_chance = 0.40 + luck * 0.05 + power * 0.001 - world["corruption"] * 0.03 - world["rift_instability"] * 0.03
                win_chance = max(0.05, min(0.95, win_chance))
                if random.random() < win_chance:
                    loot = int(hp_scale * luck * 1.8)
                    pray_mult = get_pray_boost(uid)
                    loot = int(loot * pray_mult)
                    await update_balance(uid, loot)
                    self.d["boss_kills"] += 1
                    self.d["floor"] += 1
                    self.d["energy"] = min(10, self.d["energy"] + 2)
                    self.d["skill_points"] += 2
                    adjust_sanity(self.d, random.randint(6, 15))
                    reliq = random.choice(["Crown of Ends", "Star-Shear Bridle", "Omega Hoofprint", "Heart of the Rift"])
                    self.d["relics"].append(reliq)
                    self.d["last_log"] = f"You slay the boss {boss_name}, gaining {loot} horsenncy and relic {reliq}."
                else:
                    dmg = random.randint(70, 170) + int(world["corruption"] * 25) + int(world["rift_instability"] * 90)
                    self.d["hp"] -= dmg
                    adjust_sanity(self.d, -random.randint(8, 18))
                    curse_pool = ["Shattered Courage", "Fraying Reality", "Burning Hooves", "Riftburn Scars"]
                    curse = random.choice(curse_pool)
                    self.d["curses"].append(curse)
                    if self.d["hp"] <= 0:
                        self.d["hp"] = 0
                        self.d["active"] = False
                        save_state()
                        await inter.response.edit_message(
                            embed=discord.Embed(
                                title=self.title,
                                description=f"The boss {boss_name} erases you from the floor.\nYou fall at floor {self.d['floor']}.",
                                color=discord.Color.dark_red()
                            ),
                            view=None
                        )
                        return
                    self.d["last_log"] = f"The boss {boss_name} maims you for {dmg} HP and inflicts {curse}."
                    self.d["floor"] += 1
                save_state()
                await self.refresh_message(inter)

            async def handle_invasion(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                target = pick_invasion_target(uid)
                if not target:
                    self.d["last_log"] = "An invasion rift sputters out. No target found."
                    self.d["floor"] += 1
                    save_state()
                    await self.refresh_message(inter)
                    return
                tid, td = target
                atk_power = get_power(self.d) * (1 + self.d["skills"]["might"] * 0.05)
                def_power = get_power(td) * (1 + td["skills"]["ward"] * 0.05)
                base = 0.55 + self.d["skills"]["instinct"] * 0.03 - len(self.d["curses"]) * 0.02
                base -= len(td["relics"]) * 0.01
                ratio = atk_power / max(10, atk_power + def_power)
                win_chance = base + ratio * 0.25
                win_chance = max(0.05, min(0.95, win_chance))
                steal_ratio = random.uniform(0.06, 0.20)
                target_user = get_user(tid)
                if random.random() < win_chance:
                    stolen = int(target_user["balance"] * steal_ratio)
                    target_user["balance"] = max(0, target_user["balance"] - stolen)
                    user_local = get_user(uid)
                    user_local["balance"] += stolen
                    if td["relics"]:
                        stolen_relic = random.choice(td["relics"])
                        td["relics"].remove(stolen_relic)
                        self.d["relics"].append(stolen_relic)
                        relic_text = f" and stole relic {stolen_relic}"
                    else:
                        relic_text = ""
                    adjust_sanity(self.d, -random.randint(1, 4))
                    self.d["last_log"] = f"You invade <@{tid}> and steal {stolen} horsenncy{relic_text}."
                    if self.d["invasion_shield"] < 2:
                        self.d["invasion_shield"] += 1
                else:
                    penalty = int(user["balance"] * 0.05)
                    penalty = min(penalty, user["balance"])
                    if penalty > 0:
                        await update_balance(uid, -penalty)
                    adjust_sanity(self.d, -random.randint(2, 6))
                    self.d["last_log"] = f"Your invasion against <@{tid}> fails. You lose {penalty} horsenncy."
                self.d["floor"] += 1
                save_state()
                await self.refresh_message(inter)

            async def handle_rest(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                if self.d["energy"] >= 6 and self.d["hp"] >= self.d["max_hp"] * 0.8 and self.d["sanity"] >= self.d["max_sanity"] * 0.7:
                    self.d["last_log"] = "You are already in good shape. Resting feels pointless."
                    save_state()
                    await self.refresh_message(inter)
                    return
                ambush_chance = 0.25 + world["corruption"] * 0.02 + world["rift_instability"] * 0.04
                if random.random() < ambush_chance:
                    dmg = random.randint(20, 80)
                    self.d["hp"] -= dmg
                    adjust_sanity(self.d, -random.randint(4, 9))
                    if self.d["hp"] <= 0:
                        self.d["hp"] = 0
                        self.d["active"] = False
                        save_state()
                        await inter.response.edit_message(
                            embed=discord.Embed(
                                title=self.title,
                                description=f"You were ambushed in your sleep and perish on floor {self.d['floor']}.",
                                color=discord.Color.dark_red()
                            ),
                            view=None
                        )
                        return
                    self.d["last_log"] = f"An unseen horror ambushes you while resting for {dmg} HP."
                else:
                    heal = random.randint(25, 80) + self.d["skills"]["ward"] * 8
                    self.d["hp"] = min(self.d["max_hp"], self.d["hp"] + heal)
                    self.d["energy"] = min(10, self.d["energy"] + 3)
                    adjust_sanity(self.d, random.randint(4, 10))
                    self.d["last_log"] = f"You rest uneasily, healing {heal} HP, regaining energy, and steadying your mind."
                save_state()
                await self.refresh_message(inter)

            async def handle_skills(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                if self.d["skill_points"] <= 0:
                    self.d["last_log"] = "You lack skill points to channel any growth."
                    save_state()
                    await self.refresh_message(inter)
                    return
                weights = []
                for key in ["might", "ward", "greed", "warp", "instinct"]:
                    val = self.d["skills"][key]
                    w = max(1, 4 - val)
                    if key == "warp":
                        w += self.d["rift_depth"] // 3
                    weights.append((key, w))
                pool = []
                for k, w in weights:
                    pool.extend([k] * w)
                chosen = random.choice(pool)
                self.d["skills"][chosen] += 1
                self.d["skill_points"] -= 1
                adjust_sanity(self.d, random.randint(0, 2))
                self.d["last_log"] = f"Your {chosen} grows to level {self.d['skills'][chosen]}."
                save_state()
                await self.refresh_message(inter)

            async def handle_raid(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                ensure_raid_boss()
                if self.d["raid_tokens"] <= 0:
                    self.d["last_log"] = "You have no raid tokens to join the assault."
                    save_state()
                    await self.refresh_message(inter)
                    return
                if world["raid_hp"] <= 0:
                    self.d["last_log"] = "The current raid boss is already defeated. Wait for the next one."
                    save_state()
                    await self.refresh_message(inter)
                    return
                self.d["raid_tokens"] -= 1
                power = get_power(self.d)
                luck = get_luck(self.d)
                dmg = int(power * random.uniform(0.7, 1.4) * luck)
                crit = random.random() < (0.10 + self.d["skills"]["might"] * 0.03)
                if crit:
                    dmg = int(dmg * 1.8)
                world["raid_hp"] = max(0, world["raid_hp"] - dmg)
                base_reward = int(dmg * (0.6 + luck))
                pray_mult = get_pray_boost(uid)
                base_reward = int(base_reward * pray_mult)
                await update_balance(uid, base_reward)
                adjust_sanity(self.d, random.randint(3, 8))
                if world["raid_hp"] <= 0:
                    bonus = int(world["raid_max_hp"] * 0.2)
                    bonus = int(bonus * pray_mult)
                    await update_balance(uid, bonus)
                    world["last_event"] = f"{world['raid_boss']} was slain. Raid cycle completed."
                    self.d["last_log"] = f"You deal {dmg} damage and land the final blow, gaining {base_reward + bonus} horsenncy."
                    world["raid_boss"] = None
                    world["raid_hp"] = 0
                    world["raid_max_hp"] = 0
                else:
                    self.d["last_log"] = f"You strike {world['raid_boss']} for {dmg} damage and gain {base_reward} horsenncy."
                save_state()
                await self.refresh_message(inter)

            async def handle_rift_dive(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                if self.d["hp"] <= 0:
                    self.d["active"] = False
                    save_state()
                    await inter.response.edit_message(
                        embed=discord.Embed(
                            title=self.title,
                            description="Your body is gone. The rift will not accept only a mind.",
                            color=discord.Color.dark_red()
                        ),
                        view=None
                    )
                    return
                if self.d["energy"] < 2:
                    self.d["last_log"] = "You need at least 2 energy to dive into a rift."
                    save_state()
                    await self.refresh_message(inter)
                    return
                self.d["energy"] -= 2
                self.d["rift_depth"] += 1
                world["rift_instability"] += 0.04
                world["rift_level"] += 1
                roll = random.random()
                if roll < 0.40:
                    gain = int((80 + self.d["floor"] * 18) * get_luck(self.d))
                    pray_mult = get_pray_boost(uid)
                    gain = int(gain * pray_mult)
                    await update_balance(uid, gain)
                    adjust_sanity(self.d, -random.randint(3, 7))
                    self.d["last_log"] = f"You plunge into a personal rift and drag out {gain} horsenncy before it snaps shut."
                elif roll < 0.70:
                    relics = ["Rift-Linked Crown", "Glass Ribcage", "Endless Lantern", "Gravity Knot"]
                    relic = random.choice(relics)
                    self.d["relics"].append(relic)
                    adjust_sanity(self.d, -random.randint(5, 10))
                    self.d["last_log"] = f"The rift fuses you with relic {relic}. It does not leave you unchanged."
                elif roll < 0.88:
                    mut_pool = ["Second Shadow", "Hollow Voice", "Clockwork Gaze", "Liquid Bones"]
                    mut = random.choice(mut_pool)
                    self.d["mutations"].append(mut)
                    adjust_sanity(self.d, -random.randint(6, 14))
                    self.d["last_log"] = f"The rift rewrites you with mutation {mut}."
                else:
                    adjust_sanity(self.d, -random.randint(10, 18))
                    curse = random.choice(["Unbound Echo", "Screaming Thread", "Molten Silence"])
                    self.d["curses"].append(curse)
                    self.d["last_log"] = f"The rift collapses on you, branding you with {curse} and leaving no clear reward."
                save_state()
                await self.refresh_message(inter)

            async def handle_leave(self, inter):
                if self.is_stale():
                    await inter.response.send_message("This dungeon run has already ended. Use /dungeon to start a new run.", ephemeral=True)
                    return
                self.d["active"] = False
                self.d["runs"] += 1
                base_reward = int(self.d["floor"] * 40 + len(self.d["relics"]) * 60 - len(self.d["curses"]) * 45 + self.d["rift_depth"] * 30)
                pray_mult = get_pray_boost(uid)
                exit_reward = int(max(0, base_reward) * pray_mult)
                await update_balance(uid, exit_reward)
                save_state()
                await inter.response.edit_message(
                    embed=discord.Embed(
                        title=self.title,
                        description=f"You leave the dungeon at floor {self.d['floor']} with rift depth {self.d['rift_depth']}.\nYou receive {exit_reward} horsenncy for your efforts.",
                        color=discord.Color.gold()
                    ),
                    view=None
                )

            @discord.ui.button(label="Explore", style=discord.ButtonStyle.green, row=0)
            async def explore_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.do_explore(inter)

            @discord.ui.button(label="Rest", style=discord.ButtonStyle.secondary, row=0)
            async def rest_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.handle_rest(inter)

            @discord.ui.button(label="Skills", style=discord.ButtonStyle.primary, row=0)
            async def skills_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.handle_skills(inter)

            @discord.ui.button(label="Raid Boss", style=discord.ButtonStyle.blurple, row=0)
            async def raid_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.handle_raid(inter)

            @discord.ui.button(label="Rift Dive", style=discord.ButtonStyle.secondary, row=1)
            async def rift_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.handle_rift_dive(inter)

            @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, row=1)
            async def leave_btn(self, inter: discord.Interaction, button: discord.ui.Button):
                if inter.user.id != uid:
                    await inter.response.send_message("Not your dungeon.", ephemeral=True)
                    return
                await self.handle_leave(inter)

        view = DungeonView(dungeon, session_id)
        await interaction.response.send_message(embed=view.build_embed(), view=view)


async def setup(bot):
    await bot.add_cog(Dungeon(bot))
