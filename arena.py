import random
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user, save_state, state, update_balance, get_balance, get_pray_boost

ASCII_SPRITES = {
    "🐀 Rat": r"""
     (\_/)
    ( •.•)
    /╱  ╲
    """,

    "🐁 Field Mouse": r"""
     (\_/)
    ( •.°)
    /╱  ╲
    """,

    "🐦 Sparrow": r"""
      /\ 
     (•v)
    /╱ ╲
    """,

    "🐇 Bunny": r"""
     (\_/)
    ( •ᴥ•)
    /  ╱╲
    """,

    "🦊 Fox": r"""
    /\_/\
   (•ᵔᵥᵔ)
    ╱╲ ╱
    """,

    "🦝 Raccoon": r"""
    /\_/\
   (•◕ᴥ◕)
    ╱██╲
    """,

    "🐿️ Squirrel": r"""
     (\_/)
    ( •ᴥ•)
    /╱尾╲
    """,

    "🦤 Dodo (how??)": r"""
     __
    (•ᴗ)
    / )╲
    """,

    "🐔 Chicken": r"""
     /\
    (•>)
    /||╲
    """,

    "🦆 Duck": r"""
     __
    (•>)
    / )╲
    """,

    "🐄 Cow (baby)": r"""
     /''\
    ( •ᴥ)
    / ||╲
    """,

    "🐕 Stray Dog": r"""
    /‾‾\
   ( •ᴥ)
    /╱╲
    """,

    "🐈 Wild Cat": r"""
    /\_/\
   (=•.•)
    / ╲
    """,

    "🦮 Hunting Dog": r"""
    /‾‾\
   ( •ᴥ)~
    /╱╲
    """,

    "🐖 Piglet": r"""
    (••)
   ( () )
     ╲╱
    """,

    "🦢 Swan": r"""
     __
    <• )
    /  ╲_
    """,

    "🦉 Barn Owl": r"""
    (•ᴗ•)
   /|   |\
     ╲_╱
    """,

    "🦜 Parrot": r"""
     /\
    (•▾)
    /|╲
    """,

    "🦎 Lizard": r"""
     __
    (• )
    /__╲
    """,

    "🐍 Small Snake": r"""
     /^\ 
    ( •)
    ╲_/_~
    """,

    "🦌 Deer": r"""
    /‾‾‾\
   (•  •)
     ╲_╱
    """,

    "🐗 Wild Hog": r"""
    (••)>
   (____)
     ╲╱
    """,

    "🦃 Turkey": r"""
    (•ᴗ)
   <▮▮▮>
     || 
    """,

    "🐐 Mountain Goat": r"""
    /\_/\
   (･ω )
    /‾╲
    """,

    "🐓 Rooster": r"""
     /\
    (•ⱷ)
    /||>
    """,

    "🦢 Giant Swan": r"""
     ___
    < • )
    /   ╲_
    """,

    "🦨 Skunk": r"""
    /\_/|
   ( •.•)
   /_██_╲
    """,

    "🐊 Baby Crocodile": r"""
     ____ 
    ( •_)
    /__ )
    """,

    "🐺 Wolf": r"""
    /\_/\
   ( •᷄ɷ•᷅)
    /  ╲
    """,

    "🦫 Beaver": r"""
    (•ᴗ•)
    /| |
    (_/_)
    """,

    "🦦 Otter": r"""
     (\_)
    ( •ᴥ)
     /╱
    """,

    "🐅 Young Tiger": r"""
    /\_/\
   (=ᵔᵥᵔ)
    /╳╲
    """,

    "🦘 Wallaby": r"""
     /)_
    ( •_\
     /  )
    """,

    "🐏 Ram": r"""
     @  @
    (•ᴗ )
     /‾╲
    """,

    "🦅 Eagle": r"""
     /\__
    (•> )
     /| 
    """,

    "🦩 Flamingo": r"""
      _
     (•)
      |\
     _| 
    """,

    "🦚 Peacock": r"""
    (•ᴗ)
   <▒▒▒>
     || 
    """,

    "🦡 Badger": r"""
    /‾‾\
   ( •ᴥ)
    /__╲
    """,

    "🦤 Giant Dodo": r"""
     ___
    (•ᴗ)
   /(   )
     ╲╱
    """,

    "🦭 Mini Seal": r"""
     __
    (•_)
    / )╲_
    """,

    "🐻 Bear": r"""
    /‾‾\
  (ʕ•ᴥ•ʔ)
    /‾‾╲
    """,

    "🐅 Tiger": r"""
    /\_/\
   (=｀ᗜ´=)
    /╳╳╲
    """,

    "🦏 Rhino (baby)": r"""
     __
    (•╭)
    /  ╲_
    """,

    "🦍 Gorilla": r"""
    (¯▿¯)
   /▢▢▢\
     ╲_╱
    """,

    "🦬 Buffalo": r"""
     ____ 
    (••_)
    /_||╲
    """,

    "🐘 Baby Elephant": r"""
     __
    (• ▽)
    /|  )
    """,

    "🦌 Elk": r"""
    /\  /\
   ( •  •)
     ╲__╱
    """,

    "🦈 Reef Shark": r"""
     /\__
    <•  )
     \__╱
    """,

    "🐊 Crocodile": r"""
    _____
   ( •  )
   /__  )
      ‾‾
    """,

    "🦒 Giraffe": r"""
     /‾|
    (• )
     |||
     || 
    """,

    "🦛 Hippo": r"""
    (••)
   (____)
     || 
    """,

    "🐆 Leopard": r"""
    /\_/\
   (•꘎•)
   /• •╲
    """,

    "🦃 Mutant Turkey": r"""
   (◉ᴗ◉)
   <▒▒▒▒>
     ||  
    """,

    "🦜 Tropical Macaw": r"""
     /\__
    (•▾)
     /|╲
    """,

    "🦢 Enraged Swan": r"""
     ___
    < •◣)
    /   ╲_
    """,

    "🦡 Alpha Badger": r"""
    /██\
   ( •ᴥ)
    /__╲
    """,

    "🦭 Great Seal": r"""
     ___
    (•_•)
    / ) )╲_
    """,

    "🐐 Demon Goat": r"""
    /\_/\
   ( ºᴥº)
    /‾‾╲
    """,

    "🦣 Mammoth Calf": r"""
     __
    (• ▽)
    /|██)
    """,

    "🦦 Sea Otter King": r"""
     (\_/)
    ( •ᴥ)
    /︶♛
    """,

    "🐉 Baby Dragon": r"""
    /\___/\
   ( •🔥• )
    / /\ \
    """,

    "🦅 Roc Hatchling": r"""
     /\___
    (•>  )
     /|  
    """,

    "🐲 Mini Wyvern": r"""
    /\_/\
   (•  )
    /\/\
    """,

    "🦂 Giant Scorpion": r"""
    _/‾\_
   ( •• )
   /_/ \_
    """,

    "🦖 Young T-Rex": r"""
     __
    (•ᴗ|)
    /|_|
    """,

    "🦕 Brontosaurus Hatchling": r"""
     __
    (• )
    /| )_
     |_|
    """,

    "🦍 Titan Gorilla": r"""
    (⌐■-■)
   /▢▢▢▢\
     ╲__╱
    """,

    "🐲 Lava Drake": r"""
    /\___/\
   ( •🔥 )
    / /\ \
    """,

    "🦈 Megalodon Pup": r"""
    /\____
   <•   ))
     \___╱
    """,

    "🐺 Dire Wolf": r"""
    /\_/\
   ( ⚈ɷ⚈)
    /  ╲
    """,

    "🦄 Unicorn Fawn": r"""
    /\_/\
   (•ᴗ•)>
    /  ╲
    """,

    "🐉 Forest Dragonling": r"""
    /\___/\
   ( •ᵔᵔ)
    /🌿╲
    """,

    "🐐 Chaos Goat": r"""
    /\_/\
   ( ºᴥº)~
    /‾‾╲
    """,

    "🦅 Storm Eagle": r"""
     /\___
    (•>⚡)
     /|  
    """,

    "🐗 Demon Boar": r"""
    (◣◢)
   (____)
     ╲╱
    """,

    "🐆 Shadow Panther": r"""
    /\_/\
   (= ಠ_ಠ)
    /   ╲
    """,

    "🦇 Vampire Batlord": r"""
    /\_/\
   (•ᴗ•)
   / \/╲
    """,

    "🐍 Titan Serpent": r"""
     /^\
    ( •)
    ╲_/~~~
    """,

    "🦎 Elder Lizard": r"""
     __
    (• )
    /__≈
    """,

    "🐘 Giant Elephant Spirit": r"""
     __
    (• ▽)☆
    /|  )
    """,

    "🐉 Ancient Dragon": r"""
    /\____/\
   ( •🔥•  )
    / /\   ╲
    """,

    "🐲 Celestial Wyvern": r"""
    /\_/\
   (•✧ )
    /✧╲
    """,

    "🦅 Thunder Roc": r"""
     /\____
    (•>⚡ )
     /|   
    """,

    "🦄 Eternal Unicorn": r"""
    /\_/\
   (•ᴗ•)✨
    /   ╲
    """,

    "🐺 Moon Wolf": r"""
    /\_/\
   ( •ᴥ)🌙
    /   ╲
    """,

    "🐆 Galaxy Panther": r"""
    /\_/\
   (•✦•)
    /✦╲
    """,

    "🦂 King Scorpion": r"""
    _/‾\_
   ( ◉◉ )
   /_/ \_
    """,

    "🦖 Elder T-Rex": r"""
     ___
    (•╬|)
    /|_|
    """,

    "🦕 Prime Bronto": r"""
     ___
    (• )
    /| )_
    /_|_╱
    """,

    "🐊 Abyssal Crocodile": r"""
    _____
   ( •  )
   /__  )≈
      ‾‾
    """,

    "🌑 Shadow Colossus": r"""
     ███
    (◣_◢)
    /███╲
    """,

    "🌋 Volcano Titan": r"""
     /^^\
    (🔥_🔥)
    /_  _╲
    """,

    "🌪️ Storm Leviathan": r"""
     ~~~╲
    ( ⚡ )
    ╲_~~/
    """,

    "🌌 Cosmic Dragon": r"""
    /\___/\
   ( ✦🔥✦ )
    / ✦╲
    """,

    "🔥 Phoenix": r"""
     /\ 
    (🔥)
    /╱╲
    """,
}


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
    TYPE_CHART = {
        ("fire", "beast"): 1.3,
        ("fire", "mystic"): 1.1,
        ("fire", "water"): 0.7,
        ("water", "fire"): 1.4,
        ("water", "earth"): 1.2,
        ("water", "air"): 0.8,
        ("air", "beast"): 1.2,
        ("air", "earth"): 1.3,
        ("air", "mystic"): 1.1,
        ("earth", "fire"): 1.2,
        ("earth", "air"): 0.8,
        ("earth", "beast"): 1.1,
        ("dark", "mystic"): 1.4,
        ("dark", "beast"): 1.1,
        ("dark", "fire"): 1.1,
        ("mystic", "dark"): 1.3,
        ("mystic", "beast"): 1.1,
    }

    MOVE_SETS = {
        "beast": [
            {"name": "Savage Pounce", "element": "beast", "kind": "attack", "power": 1.0, "accuracy": 0.95, "status": None, "status_chance": 0.0},
            {"name": "Rending Claws", "element": "beast", "kind": "attack", "power": 1.15, "accuracy": 0.9, "status": None, "status_chance": 0.0},
            {"name": "War Howl", "element": "beast", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "atk_up", "status_chance": 1.0},
        ],
        "fire": [
            {"name": "Flame Burst", "element": "fire", "kind": "attack", "power": 1.1, "accuracy": 0.93, "status": "burn", "status_chance": 0.35},
            {"name": "Inferno Claw", "element": "fire", "kind": "attack", "power": 1.25, "accuracy": 0.85, "status": "burn", "status_chance": 0.45},
            {"name": "Blazing Aura", "element": "fire", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "atk_up", "status_chance": 1.0},
        ],
        "water": [
            {"name": "Aqua Slash", "element": "water", "kind": "attack", "power": 1.05, "accuracy": 0.96, "status": None, "status_chance": 0.0},
            {"name": "Tidal Crash", "element": "water", "kind": "attack", "power": 1.2, "accuracy": 0.88, "status": None, "status_chance": 0.0},
            {"name": "Restorative Tide", "element": "water", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "regen", "status_chance": 1.0},
        ],
        "air": [
            {"name": "Sky Cutter", "element": "air", "kind": "attack", "power": 1.05, "accuracy": 0.95, "status": None, "status_chance": 0.0},
            {"name": "Storm Dive", "element": "air", "kind": "attack", "power": 1.2, "accuracy": 0.88, "status": "stun", "status_chance": 0.25},
            {"name": "Tailwind Rush", "element": "air", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "spd_up", "status_chance": 1.0},
        ],
        "earth": [
            {"name": "Quake Slam", "element": "earth", "kind": "attack", "power": 1.15, "accuracy": 0.9, "status": "stun", "status_chance": 0.2},
            {"name": "Stone Crush", "element": "earth", "kind": "attack", "power": 1.25, "accuracy": 0.85, "status": None, "status_chance": 0.0},
            {"name": "Iron Hide", "element": "earth", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "def_up", "status_chance": 1.0},
        ],
        "dark": [
            {"name": "Night Fang", "element": "dark", "kind": "attack", "power": 1.1, "accuracy": 0.93, "status": "bleed", "status_chance": 0.3},
            {"name": "Shadow Rend", "element": "dark", "kind": "attack", "power": 1.25, "accuracy": 0.85, "status": "bleed", "status_chance": 0.4},
            {"name": "Abyssal Curse", "element": "dark", "kind": "attack", "power": 0.9, "accuracy": 0.9, "status": "poison", "status_chance": 0.6},
        ],
        "mystic": [
            {"name": "Radiant Horn", "element": "mystic", "kind": "attack", "power": 1.1, "accuracy": 0.95, "status": None, "status_chance": 0.0},
            {"name": "Starfall Lance", "element": "mystic", "kind": "attack", "power": 1.25, "accuracy": 0.9, "status": "stun", "status_chance": 0.25},
            {"name": "Celestial Grace", "element": "mystic", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "regen", "status_chance": 1.0},
        ],
    }

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

    def infer_element(self, name):
        n = name.lower()
        if "dragon" in n or "wyvern" in n or "drake" in n or "phoenix" in n or "lava" in n or "volcano" in n:
            return "fire"
        if "shark" in n or "seal" in n or "otter" in n or "crocodile" in n or "hippo" in n or "reef" in n or "megalodon" in n or "leviathan" in n:
            return "water"
        if "eagle" in n or "sparrow" in n or "owl" in n or "roc" in n or "parrot" in n or "macaw" in n or "swan" in n or "duck" in n or "flamingo" in n or "peacock" in n:
            return "air"
        if "rhino" in n or "mammoth" in n or "elk" in n or "buffalo" in n or "boar" in n or "hog" in n or "ram" in n or "goat" in n or "titan" in n or "colossus" in n:
            return "earth"
        if "shadow" in n or "demon" in n or "abyss" in n or "vampire" in n or "moon" in n or "king scorpion" in n or "scorpion" in n:
            return "dark"
        if "unicorn" in n or "spirit" in n or "ancient" in n or "celestial" in n or "eternal" in n or "prime" in n or "cosmic" in n or "galaxy" in n or "phoenix" in n:
            return "mystic"
        return "beast"

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
        world_msg = f"Season {self.world['season']} | Chaos {self.world['chaos']:.2f}\n{self.world['last_event']}"
        team_text = "None" if not loadout else ", ".join(self.pet_name(pet) for pet in loadout)
        embed = discord.Embed(
            title="🏟️ HORSEY ARENA — LOBBY",
            description=(
                f"Rating: {rating}\n"
                f"Tokens: {tokens}\n"
                f"Crowns: {crowns}\n"
                f"Wins: {wins} | Losses: {losses} | Streak: {streak}\n"
                f"Level: {level} ({xp} XP)\n\n"
                f"Team Loadout: {team_text}\n\n"
                f"{log}"
            ),
            color=discord.Color.gold()
        )
        embed.add_field(name="Arena World", value=world_msg, inline=False)
        return embed

    async def refresh(self, inter):
        await inter.response.edit_message(embed=self.render_lobby(), view=self)

    @discord.ui.button(label="Fight Match", style=discord.ButtonStyle.green)
    async def btn_fight(self, inter, btn):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        if self.arena["tokens"] <= 0:
            return await inter.response.send_message("You have no fight tokens left.", ephemeral=True)
        await self.start_match(inter)

    @discord.ui.button(label="Edit Team", style=discord.ButtonStyle.blurple)
    async def btn_edit(self, inter, btn):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        await self.edit_team(inter)

    @discord.ui.button(label="View Ladder", style=discord.ButtonStyle.secondary)
    async def btn_ladder(self, inter, btn):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        await self.show_ladder(inter)

    @discord.ui.button(label="Leave Arena", style=discord.ButtonStyle.red)
    async def btn_leave(self, inter, btn):
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

    def render_sprite(self, name):
        s = ASCII_SPRITES.get(name)
        if not s:
            return name
        lines = [l.rstrip() for l in s.split("\n")]
        width = 12
        out = []
        for ln in lines:
            if not ln.strip():
                continue
            pad = (width - len(ln)) // 2
            out.append(" " * pad + ln)
        return "\n".join(out)

    def hp_bar(self, hp, max_hp):
        if max_hp <= 0:
            max_hp = 1
        pct = max(0, hp) / max_hp
        fill = int(pct * 10)
        return "[" + "█" * fill + " " * (10 - fill) + f"] {max(0,int(hp))}/{int(max_hp)}"

    def format_field(self, p, o):
        lines = []
        lines.append(f"    {o['name']}  ({o['element']})")
        lines.append(f"    {self.hp_bar(o['hp'], o['max_hp'])}")
        o_s = self.render_sprite(o["name"]).split("\n")
        for ln in o_s:
            if ln.strip():
                lines.append("    " + ln)
        lines.append("")
        lines.append(f"{p['name']}  ({p['element']})")
        lines.append(self.hp_bar(p["hp"], p["max_hp"]))
        p_s = self.render_sprite(p["name"]).split("\n")
        for ln in p_s:
            if ln.strip():
                lines.append(ln)
        return "\n".join(lines)

    async def animate(self, inter, p, o, text):
        field = self.format_field(p, o)
        await inter.edit_original_response(content=f"```{field}\n\n{text}```")

    def get_moves_for(self, unit):
        el = unit.get("element", "beast")
        return self.MOVE_SETS.get(el, self.MOVE_SETS["beast"])

    def type_multiplier(self, move_elem, target_elem):
        if move_elem is None or target_elem is None:
            return 1.0
        return self.TYPE_CHART.get((move_elem, target_elem), 1.0)

    async def start_match(self, inter):
        self.arena["tokens"] -= 1
        self.arena["in_battle"] = True
        player_team = list(self.arena["loadout"])
        if not player_team:
            return await inter.response.send_message("You have no team selected.", ephemeral=True)
        opponent_team = random.sample(list(ASCII_SPRITES.keys()), k=5)
        self.arena["last_opponent"] = opponent_team
        pstats = self.build_team_stats(player_team)
        ostats = self.build_team_stats([{"name": x} for x in opponent_team])
        for u in pstats + ostats:
            u["max_hp"] = u["hp"]
            u["element"] = self.infer_element(u["name"])
            u["status"] = None
            u["atk_mod"] = 1.0
            u["def_mod"] = 1.0
            u["spd_mod"] = 1.0
            u["status_timer"] = 0
        await inter.response.send_message(content="```Battle starting...```")
        result, log = await self.simulate_battle(inter, pstats, ostats)
        await self.process_match_result(inter, result, log, opponent_team)

    def next_alive_index(self, team, start_idx):
        n = len(team)
        i = start_idx
        while i < n:
            if team[i]["hp"] > 0:
                return i
            i += 1
        return None

    async def simulate_battle(self, inter, pteam, oteam):
        log = []
        p_idx = 0
        o_idx = 0
        round_no = 1
        while True:
            p_idx = self.next_alive_index(pteam, p_idx)
            o_idx = self.next_alive_index(oteam, o_idx)
            if p_idx is None:
                return "loss", log
            if o_idx is None:
                return "win", log
            p = pteam[p_idx]
            o = oteam[o_idx]
            order = []
            p_speed = p["speed"] * p["spd_mod"] + random.uniform(0, 5)
            o_speed = o["speed"] * o["spd_mod"] + random.uniform(0, 5)
            if p_speed >= o_speed:
                order = ["p", "o"]
            else:
                order = ["o", "p"]
            for side in order:
                if p["hp"] <= 0 or o["hp"] <= 0:
                    break
                attacker = p if side == "p" else o
                defender = o if side == "p" else p
                if attacker["hp"] <= 0:
                    continue
                moves = self.get_moves_for(attacker)
                move = random.choice(moves)
                text_lines = [f"Round {round_no}", f"{attacker['name']} used {move['name']}!"]
                if move["kind"] == "buff":
                    if move["status"] == "atk_up":
                        attacker["atk_mod"] *= 1.25
                        text_lines.append(f"{attacker['name']}'s power rose!")
                    elif move["status"] == "def_up":
                        attacker["def_mod"] *= 1.25
                        text_lines.append(f"{attacker['name']}'s defense rose!")
                    elif move["status"] == "spd_up":
                        attacker["spd_mod"] *= 1.25
                        text_lines.append(f"{attacker['name']}'s speed rose!")
                    elif move["status"] == "regen":
                        attacker["status"] = "regen"
                        attacker["status_timer"] = 3
                        text_lines.append(f"{attacker['name']} is surrounded by healing energy!")
                    log.extend(text_lines)
                    await self.animate(inter, p, o, "\n".join(text_lines))
                    await asyncio.sleep(1.0)
                else:
                    if attacker["status"] == "stun":
                        text_lines.append(f"{attacker['name']} is stunned and cannot move!")
                        attacker["status"] = None
                        attacker["status_timer"] = 0
                        log.extend(text_lines)
                        await self.animate(inter, p, o, "\n".join(text_lines))
                        await asyncio.sleep(1.0)
                    else:
                        if random.random() > move["accuracy"]:
                            text_lines.append("But it missed!")
                            log.extend(text_lines)
                            await self.animate(inter, p, o, "\n".join(text_lines))
                            await asyncio.sleep(1.0)
                        else:
                            base = attacker["power"] * attacker["atk_mod"] - defender["def"] * defender["def_mod"]
                            if base < 5:
                                base = 5
                            crit = False
                            if random.random() < attacker["crit"]:
                                crit = True
                                base *= 1.7
                            stab = 1.2 if move["element"] == attacker["element"] else 1.0
                            type_mult = self.type_multiplier(move["element"], defender["element"])
                            dmg = int(base * move["power"] * stab * type_mult * random.uniform(0.85, 1.0))
                            defender["hp"] -= dmg
                            eff_text = ""
                            if type_mult > 1.25:
                                eff_text = "It's super effective!"
                            elif type_mult < 0.9:
                                eff_text = "It's not very effective..."
                            text_lines.append(f"It dealt {dmg} damage.")
                            if crit:
                                text_lines.append("A critical hit!")
                            if eff_text:
                                text_lines.append(eff_text)
                            if move["status"] in ("burn", "poison", "bleed", "stun") and defender["hp"] > 0:
                                if random.random() < move["status_chance"]:
                                    defender["status"] = move["status"]
                                    if move["status"] == "burn":
                                        defender["status_timer"] = 3
                                        text_lines.append(f"{defender['name']} was burned!")
                                    elif move["status"] == "poison":
                                        defender["status_timer"] = 4
                                        text_lines.append(f"{defender['name']} was poisoned!")
                                    elif move["status"] == "bleed":
                                        defender["status_timer"] = 3
                                        text_lines.append(f"{defender['name']} is bleeding!")
                                    elif move["status"] == "stun":
                                        defender["status_timer"] = 1
                                        text_lines.append(f"{defender['name']} was stunned!")
                            if defender["hp"] <= 0:
                                defender["hp"] = 0
                                text_lines.append(f"{defender['name']} has fainted!")
                            log.extend(text_lines)
                            await self.animate(inter, p, o, "\n".join(text_lines))
                            await asyncio.sleep(1.1)
                            if defender["hp"] <= 0:
                                break
            for unit in [p, o]:
                if unit["hp"] <= 0:
                    continue
                if unit["status"] in ("burn", "poison", "bleed", "regen"):
                    if unit["status"] == "burn":
                        dot = max(1, int(unit["max_hp"] * 0.06))
                        unit["hp"] -= dot
                        log.append(f"{unit['name']} is hurt by its burns ({dot}).")
                    elif unit["status"] == "poison":
                        dot = max(1, int(unit["max_hp"] * 0.07))
                        unit["hp"] -= dot
                        log.append(f"{unit['name']} is hurt by poison ({dot}).")
                    elif unit["status"] == "bleed":
                        dot = max(1, int(unit["max_hp"] * 0.08))
                        unit["hp"] -= dot
                        log.append(f"{unit['name']} is bleeding ({dot}).")
                    elif unit["status"] == "regen":
                        heal = max(1, int(unit["max_hp"] * 0.06))
                        unit["hp"] = min(unit["max_hp"], unit["hp"] + heal)
                        log.append(f"{unit['name']} regains {heal} HP!")
                    unit["status_timer"] -= 1
                    if unit["status_timer"] <= 0 and unit["status"] in ("burn", "poison", "bleed", "regen"):
                        unit["status"] = None
            if p["hp"] <= 0:
                p_idx += 1
            if o["hp"] <= 0:
                o_idx += 1
            round_no += 1

    async def process_match_result(self, inter, result, log, opponent):
        rating = self.arena["rating"]
        xp = self.arena["xp"]
        level = self.arena["level"]
        streak = self.arena["streak"]
        if result == "win":
            delta = random.randint(18, 32)
            xp_gain = random.randint(30, 55)
            crowns = random.randint(0, 2)
            rating += delta
            xp += xp_gain
            streak += 1
            self.arena["wins"] += 1
            self.arena["crowns"] += crowns
            self.world["chaos"] += 0.03
            res = f"Victory!\nRating +{delta}\nXP +{xp_gain}\nCrowns +{crowns}"
        elif result == "loss":
            delta = -random.randint(10, 24)
            xp_gain = random.randint(12, 26)
            rating += delta
            xp += xp_gain
            streak = 0
            self.arena["losses"] += 1
            self.world["chaos"] += 0.015
            res = f"Defeat.\nRating {delta}\nXP +{xp_gain}"
        else:
            xp_gain = random.randint(8, 16)
            xp += xp_gain
            res = f"Draw.\nXP +{xp_gain}"
        while xp >= 100:
            xp -= 100
            level += 1
            self.arena["crowns"] += 1
            self.world["chaos"] += 0.05
        self.arena["rating"] = max(0, rating)
        self.arena["xp"] = xp
        self.arena["level"] = level
        self.arena["streak"] = streak
        self.arena["last_log"] = res
        self.world["total_matches"] += 1
        if self.world["chaos"] > 5:
            self.world["season"] += 1
            self.world["chaos"] = 0
            self.world["last_event"] = "A new Arena Season begins!"
        save_state()
        battle_text = "\n".join(log[-20:])
        opp_text = ", ".join(opponent)
        embed = discord.Embed(
            title="🏟️ ARENA MATCH RESULT",
            description=f"Result: {result.upper()}\nOpponent Team: {opp_text}\n\n{res}\n\nBattle Log (Last 20 events):\n{battle_text}",
            color=discord.Color.gold()
        )
        await inter.edit_original_response(content=None, embed=embed)

    async def edit_team(self, inter):
        if not self.owned:
            return await inter.response.send_message("You own no animals.", ephemeral=True)
        options = []
        for pet in self.owned:
            nm = pet["name"] if isinstance(pet, dict) else str(pet)
            options.append(discord.SelectOption(label=nm, value=nm))
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
        sorted_pairs = sorted(ladder.items(), key=lambda x: x[1], reverse=True)[:10]
        lines = []
        for i, (pid, rating) in enumerate(sorted_pairs, 1):
            try:
                user_obj = await inter.client.fetch_user(int(pid))
                name = user_obj.display_name
            except:
                name = f"User {pid}"
            lines.append(f"#{i} {name} — {rating}")
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
            "might": {"name": "Might Emblem", "cost": 3, "key": "power_boost", "amount": 0.05},
            "haste": {"name": "Haste Emblem", "cost": 3, "key": "speed_boost", "amount": 0.07},
            "ward": {"name": "Ward Emblem", "cost": 3, "key": "def_boost", "amount": 0.07},
            "luck": {"name": "Lucky Emblem", "cost": 4, "key": "crit_boost", "amount": 0.03}
        }
        options = [
            discord.SelectOption(label=data["name"], value=key, description=f"Cost {data['cost']} crowns")
            for key, data in items.items()
        ]
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
                return await sel_inter.response.send_message("Not enough crowns.", ephemeral=True)
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
            description=f"You have {self.arena['crowns']} crowns.\nChoose a permanent Arena buff to purchase.",
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
    async def btn_shop(self, inter, btn):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        await self.crown_shop(inter)

async def setup(bot):
    await bot.add_cog(HorseyArena(bot))
