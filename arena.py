import random
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from economy_shared import state, save_state
from economy import get_user, update_balance, get_balance, get_pray_boost

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


EVOLUTIONS = {
    "🐺 Wolf": "🐺 Dire Wolf",
    "🐺 Dire Wolf": "🐺 Moon Wolf",
    "🐆 Leopard": "🐆 Galaxy Panther",
    "🐆 Galaxy Panther": "🌌 Cosmic Dragon",
    "🐉 Baby Dragon": "🐲 Lava Drake",
    "🐲 Lava Drake": "🐉 Ancient Dragon",
    "🦅 Eagle": "🦅 Storm Eagle",
    "🦅 Storm Eagle": "🦅 Thunder Roc",
    "🦭 Mini Seal": "🦭 Great Seal",
    "🦡 Badger": "🦡 Alpha Badger",
    "🐐 Demon Goat": "🐐 Chaos Goat",
    "🦕 Brontosaurus Hatchling": "🦕 Prime Bronto",
    "🦖 Young T-Rex": "🦖 Elder T-Rex",
    "🐊 Crocodile": "🐊 Abyssal Crocodile",
    "🐻 Bear": "🌑 Shadow Colossus",
    "🐘 Baby Elephant": "🐘 Giant Elephant Spirit",
    "🦍 Gorilla": "🦍 Titan Gorilla",
    "🔥 Phoenix": "🔥 Phoenix",
    "🦄 Unicorn Fawn": "🦄 Eternal Unicorn",
}

ARENA_MUTATORS = [
    ("Bloodsport", "All damage increased, healing reduced.", 1.25, 0.7),
    ("Iron Wall", "Defense and shields stronger.", 0.9, 1.3),
    ("Arcane Storm", "Crit rate higher, status effects stronger.", 1.1, 1.0),
    ("Chaotic Whirl", "Random stat swings each round.", 1.0, 1.0),
    ("Blessed Grounds", "Healing stronger, damage slightly lower.", 0.9, 1.25),
]

class HorseyArena(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="arena", description="Enter the Horsey Arena auto-battler.")
    async def arena(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)
        arena = user.setdefault("arena", {})
        now = datetime.datetime.utcnow().date().isoformat()
        if arena.get("last_token_reset") != now:
            arena["tokens"] = 3
            arena["last_token_reset"] = now
        arena["rating"] = arena.get("rating", 1000)
        arena["tokens"] = arena.get("tokens", 3)
        arena["crowns"] = arena.get("crowns", 0)
        arena["wins"] = arena.get("wins", 0)
        arena["losses"] = arena.get("losses", 0)
        arena["streak"] = arena.get("streak", 0)
        arena["level"] = arena.get("level", 1)
        arena["xp"] = arena.get("xp", 0)
        arena["last_log"] = arena.get("last_log", "The Arena gate creaks open.")
        arena["in_battle"] = False
        arena["loadout"] = arena.get("loadout", [])
        arena["passives"] = arena.get("passives", {})
        arena["evolved"] = arena.get("evolved", {})
        arena["last_mutator"] = arena.get("last_mutator", None)
        arena["last_ult"] = arena.get("last_ult", "")
        owned = user.setdefault("owned_animals", [])
        team = user.setdefault("team", [])
        world = state.setdefault("arena_world", {})
        world["season"] = world.get("season", 1)
        world["chaos"] = world.get("chaos", 0.0)
        world["total_matches"] = world.get("total_matches", 0)
        world["last_champion"] = world.get("last_champion", None)
        world["last_event"] = world.get("last_event", "The sands are quiet.")
        world["ladder"] = world.get("ladder", {})
        world["mutator"] = world.get("mutator", None)
        if not arena["loadout"]:
            arena["loadout"] = list(team[:5])
        view = ArenaView(uid=uid, arena=arena, world=world, owned_animals=owned, team_ref=team)
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
    ROLES = ["tank", "striker", "support", "healer", "trickster"]
    RARITIES = [
        ("Common", 1.0),
        ("Uncommon", 1.10),
        ("Rare", 1.25),
        ("Epic", 1.45),
        ("Legendary", 1.75),
    ]
    ENVIRONMENTS = [
        ("Blazing Sun", "fire", "water"),
        ("Raging Storm", "air", "earth"),
        ("Tidal Surge", "water", "fire"),
        ("Eclipse", "dark", "mystic"),
    ]
    MOVE_SETS = {
        "beast": [
            {"name": "Savage Pounce", "element": "beast", "kind": "attack", "power": 1.0, "accuracy": 0.96, "status": None, "status_chance": 0.0},
            {"name": "Rending Claws", "element": "beast", "kind": "attack", "power": 1.20, "accuracy": 0.9, "status": "bleed", "status_chance": 0.35},
            {"name": "War Howl", "element": "beast", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "atk_up", "status_chance": 1.0},
        ],
        "fire": [
            {"name": "Flame Burst", "element": "fire", "kind": "attack", "power": 1.10, "accuracy": 0.93, "status": "burn", "status_chance": 0.4},
            {"name": "Inferno Claw", "element": "fire", "kind": "attack", "power": 1.30, "accuracy": 0.85, "status": "burn", "status_chance": 0.5},
            {"name": "Blazing Aura", "element": "fire", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "atk_up", "status_chance": 1.0},
        ],
        "water": [
            {"name": "Aqua Slash", "element": "water", "kind": "attack", "power": 1.05, "accuracy": 0.97, "status": None, "status_chance": 0.0},
            {"name": "Tidal Crash", "element": "water", "kind": "attack", "power": 1.20, "accuracy": 0.9, "status": "stun", "status_chance": 0.2},
            {"name": "Restorative Tide", "element": "water", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "regen", "status_chance": 1.0},
        ],
        "air": [
            {"name": "Sky Cutter", "element": "air", "kind": "attack", "power": 1.05, "accuracy": 0.96, "status": None, "status_chance": 0.0},
            {"name": "Storm Dive", "element": "air", "kind": "attack", "power": 1.20, "accuracy": 0.88, "status": "stun", "status_chance": 0.3},
            {"name": "Tailwind Rush", "element": "air", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "spd_up", "status_chance": 1.0},
        ],
        "earth": [
            {"name": "Quake Slam", "element": "earth", "kind": "attack", "power": 1.15, "accuracy": 0.9, "status": "stun", "status_chance": 0.2},
            {"name": "Stone Crush", "element": "earth", "kind": "attack", "power": 1.30, "accuracy": 0.85, "status": None, "status_chance": 0.0},
            {"name": "Iron Hide", "element": "earth", "kind": "buff", "power": 0.0, "accuracy": 1.0, "status": "def_up", "status_chance": 1.0},
        ],
        "dark": [
            {"name": "Night Fang", "element": "dark", "kind": "attack", "power": 1.1, "accuracy": 0.93, "status": "bleed", "status_chance": 0.4},
            {"name": "Shadow Rend", "element": "dark", "kind": "attack", "power": 1.25, "accuracy": 0.86, "status": "poison", "status_chance": 0.45},
            {"name": "Abyssal Curse", "element": "dark", "kind": "attack", "power": 0.95, "accuracy": 0.9, "status": "poison", "status_chance": 0.65},
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
        self.current_env = self.pick_environment()

    def pick_environment(self):
        idx = (self.world["season"] - 1) % len(self.ENVIRONMENTS)
        return self.ENVIRONMENTS[idx]

    def pet_name(self, pet):
        if isinstance(pet, dict):
            return pet.get("name", "Unknown")
        return str(pet)

    def infer_element(self, name):
        n = name.lower()
        if any(k in n for k in ["dragon", "wyvern", "drake", "phoenix", "lava", "volcano"]):
            return "fire"
        if any(k in n for k in ["shark", "seal", "otter", "crocodile", "hippo", "reef", "megalodon", "leviathan"]):
            return "water"
        if any(k in n for k in ["eagle", "sparrow", "owl", "roc", "parrot", "macaw", "swan", "duck", "flamingo", "peacock"]):
            return "air"
        if any(k in n for k in ["rhino", "mammoth", "elk", "buffalo", "boar", "hog", "ram", "goat", "titan", "colossus"]):
            return "earth"
        if any(k in n for k in ["shadow", "demon", "abyss", "vampire", "moon", "king scorpion", "scorpion"]):
            return "dark"
        if any(k in n for k in ["unicorn", "spirit", "ancient", "celestial", "eternal", "prime", "cosmic", "galaxy", "phoenix"]):
            return "mystic"
        return "beast"

    def assign_role_rarity(self, name):
        base = sum(ord(c) for c in name.lower())
        role = self.ROLES[base % len(self.ROLES)]
        rarity_idx = (base // 5) % len(self.RARITIES)
        rarity, mult = self.RARITIES[rarity_idx]
        return role, rarity, mult

    def assign_ability(self, name, element, role):
        nl = name.lower()
        if "phoenix" in nl:
            return "rebirth", "Rebirth"
        if "wolf" in nl or "dire" in nl or "moon wolf" in nl:
            return "pack_hunter", "Pack Hunter"
        if "goat" in nl or "demon" in nl or "chaos" in nl:
            return "berserker", "Berserker"
        if "unicorn" in nl:
            return "aura_heal", "Blessing Aura"
        if "dragon" in nl or "wyvern" in nl or "drake" in nl:
            return "scales", "Draconic Scales"
        if "titan" in nl or "colossus" in nl or "leviathan" in nl:
            return "bulwark", "Titanic Bulwark"
        if role == "healer":
            return "healer", "Mender's Grace"
        if role == "support":
            return "speed_aura", "Tailwind Banner"
        if role == "tank":
            return "guard", "Guardian's Oath"
        if role == "trickster":
            return "hex", "Chaotic Hex"
        if role == "striker":
            return "finisher", "Executioner"
        return "none", "None"

    def hp_bar(self, hp, max_hp, width=18):
        if max_hp <= 0:
            max_hp = 1
        hp = max(0, int(hp))
        max_hp = int(max_hp)
        ratio = hp / max_hp
        filled = int(ratio * width)
        empty = width - filled
        if ratio > 0.66:
            fill_char = "█"
        elif ratio > 0.33:
            fill_char = "▓"
        else:
            fill_char = "▒"
        bar = fill_char * filled + "·" * empty
        pct = int(ratio * 100)
        return f"{bar} {hp}/{max_hp} ({pct}%)"

    def render_sprite(self, name):
        s = ASCII_SPRITES.get(name)
        if not s:
            return name
        lines = [l.rstrip() for l in s.split("\n")]
        width = 18
        out = []
        for ln in lines:
            if not ln.strip():
                continue
            pad = max(0, (width - len(ln)) // 2)
            out.append(" " * pad + ln)
        return "\n".join(out)

    def format_field(self, p, o, p_offset=0, o_offset=0):
        lines = []
        o_prefix = " " * o_offset
        p_prefix = " " * p_offset
        lines.append(f"{o_prefix}{o['name']}  ({o['rarity']} {o['role']} {o['element']})")
        lines.append(f"{o_prefix}{self.hp_bar(o['hp'], o['max_hp'])}")
        o_s = self.render_sprite(o["name"]).split("\n")
        for ln in o_s:
            ln = ln.rstrip()
            if ln:
                lines.append(o_prefix + ln)
        lines.append("")
        lines.append(f"{p_prefix}{p['name']}  ({p['rarity']} {p['role']} {p['element']})")
        lines.append(f"{p_prefix}{self.hp_bar(p['hp'], p['max_hp'])}")
        p_s = self.render_sprite(p["name"]).split("\n")
        for ln in p_s:
            ln = ln.rstrip()
            if ln:
                lines.append(p_prefix + ln)
        return "\n".join(lines)

    async def animate(self, inter, p, o, text, p_offset=0, o_offset=0):
        field = self.format_field(p, o, p_offset=p_offset, o_offset=o_offset)
        await inter.edit_original_response(content=f"```{field}\n\n{text}```", embed=None)

    async def play_attack_animation(self, inter, attacker, defender, side, text):
        lines = text.split("\n")
        headline = lines[0] if lines else text
        frames = []
        frames.append((0, 0, headline))
        if side == "p":
            frames.append((2, 0, headline))
            frames.append((5, 0, text))
            frames.append((1, 0, text))
        else:
            frames.append((0, 2, headline))
            frames.append((0, 5, text))
            frames.append((0, 1, text))
        for i, (p_off, o_off, txt) in enumerate(frames):
            await self.animate(inter, attacker, defender, txt, p_offset=p_off, o_offset=o_off)
            await asyncio.sleep(0.18 if i < len(frames) - 1 else 0.08)

    async def play_ultimate_animation(self, inter, attacker, defender, side, title_lines):
        top = "═" * 31
        mid = "\n".join(title_lines)
        box = f"{top}\n{mid}\n{top}"
        p = attacker
        o = defender
        field = self.format_field(p, o, p_offset=0, o_offset=0)
        await inter.edit_original_response(content=f"```{box}\n\n{field}```", embed=None)
        await asyncio.sleep(0.7)

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
        env_name, env_boost, env_nerf = self.current_env
        mut = self.world.get("mutator")
        mut_text = "None active."
        if mut:
            mut_name, mut_desc, _, _ = mut
            mut_text = f"{mut_name}: {mut_desc}"
        world_msg = (
            f"Season {self.world['season']} | Chaos {self.world['chaos']:.2f}\n"
            f"{self.world['last_event']}\n\n"
            f"Environment: **{env_name}** (boosts `{env_boost}`, weakens `{env_nerf}`)\n"
            f"Mutator: **{mut_text}**"
        )
        if not loadout:
            team_text = "None (use Edit Team to pick up to 5 animals)."
        else:
            team_bits = []
            for pet in loadout:
                nm = self.pet_name(pet)
                el = self.infer_element(nm)
                role, rarity, _ = self.assign_role_rarity(nm)
                team_bits.append(f"{nm} ({rarity} {role}, {el})")
            team_text = "\n".join(team_bits)
        embed = discord.Embed(
            title="🏟️ HORSEY ARENA — LOBBY",
            description=(
                f"Rating: **{rating}**\n"
                f"Tokens: **{tokens}**\n"
                f"Crowns: **{crowns}**\n"
                f"Wins: **{wins}** | Losses: **{losses}** | Streak: **{streak}**\n"
                f"Level: **{level}** ({xp} XP)\n\n"
                f"__Team Loadout:__\n{team_text}\n\n"
                f"__Last Result:__\n{log}"
            ),
            color=discord.Color.gold()
        )
        embed.add_field(name="Arena World", value=world_msg, inline=False)
        last_ult = self.arena.get("last_ult")
        if last_ult:
            embed.add_field(name="Last Ultimate", value=last_ult, inline=False)
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

    @discord.ui.button(label="Crown Shop", style=discord.ButtonStyle.secondary)
    async def btn_shop(self, inter, btn):
        if inter.user.id != self.uid:
            return await inter.response.send_message("Not your Arena.", ephemeral=True)
        await self.crown_shop(inter)

    def build_team_stats(self, team, is_player):
        stats = []
        passives = self.arena.setdefault("passives", {})
        power_mult = 1.0 + passives.get("power_boost", 0.0)
        speed_mult = 1.0 + passives.get("speed_boost", 0.0)
        def_mult = 1.0 + passives.get("def_boost", 0.0)
        crit_bonus = passives.get("crit_boost", 0.0)
        chaos_factor = 1.0 + self.world["chaos"] * 0.12
        evolved_map = self.arena.get("evolved", {})
        for unit in team:
            raw_name = unit["name"] if isinstance(unit, dict) else str(unit)
            name = evolved_map.get(raw_name, raw_name)
            base_power = random.randint(40, 90)
            base_speed = random.randint(20, 65)
            base_def = random.randint(15, 45)
            base_hp = base_power * 2 + random.randint(10, 40)
            role, rarity, rarity_mult = self.assign_role_rarity(name)
            element = self.infer_element(name)
            ability_id, ability_name = self.assign_ability(name, element, role)
            if role == "tank":
                base_hp *= 1.25
                base_def *= 1.25
                base_speed *= 0.85
            elif role == "striker":
                base_power *= 1.25
                base_speed *= 1.10
                base_def *= 0.9
            elif role == "support":
                base_speed *= 1.15
                base_def *= 1.05
            elif role == "healer":
                base_hp *= 1.10
                base_def *= 1.10
                base_power *= 0.9
            elif role == "trickster":
                base_speed *= 1.2
                base_def *= 0.9
            base_hp = int(base_hp * rarity_mult * chaos_factor)
            base_power = int(base_power * rarity_mult * chaos_factor * power_mult)
            base_speed = int(base_speed * rarity_mult * speed_mult)
            base_def = int(base_def * rarity_mult * def_mult)
            crit = random.uniform(0.05, 0.17) + crit_bonus
            if role == "striker":
                crit += 0.05
            if crit > 0.6:
                crit = 0.6
            status_resist = random.uniform(0.0, 0.20)
            if role == "tank":
                status_resist += 0.1
            stats.append({
                "name": name,
                "element": element,
                "role": role,
                "rarity": rarity,
                "ability_id": ability_id,
                "ability_name": ability_name,
                "hp": base_hp,
                "max_hp": base_hp,
                "power": base_power,
                "speed": base_speed,
                "def": base_def,
                "crit": crit,
                "status_resist": status_resist,
                "status": None,
                "status_timer": 0,
                "atk_mod": 1.0,
                "def_mod": 1.0,
                "spd_mod": 1.0,
                "shield": 0,
                "has_rebirthed": False,
                "ult_charge": 0,
                "ult_ready": False,
                "clutch": rarity in ("Common", "Uncommon"),
                "clutch_used": False,
            })
        return stats

    def analyze_synergies(self, team):
        elements = {}
        roles = {}
        rarities = {}
        for u in team:
            elements[u["element"]] = elements.get(u["element"], 0) + 1
            roles[u["role"]] = roles.get(u["role"], 0) + 1
            rarities[u["rarity"]] = rarities.get(u["rarity"], 0) + 1
        bonuses = []
        for el, cnt in elements.items():
            if cnt >= 3:
                bonuses.append(("elem", el, cnt))
        for rl, cnt in roles.items():
            if cnt >= 3:
                bonuses.append(("role", rl, cnt))
        for r, cnt in rarities.items():
            if r in ("Epic", "Legendary") and cnt >= 2:
                bonuses.append(("rarity", r, cnt))
        return bonuses

    def apply_synergies_to_team(self, team, synergies, log_prefix):
        lines = []
        for kind, val, cnt in synergies:
            if kind == "elem":
                if val == "fire":
                    for u in team:
                        if u["element"] == "fire":
                            u["power"] = int(u["power"] * 1.10)
                    lines.append(f"{log_prefix} Fire pack: fire power up.")
                elif val == "water":
                    for u in team:
                        if u["element"] == "water":
                            u["max_hp"] = int(u["max_hp"] * 1.08)
                            u["hp"] = u["max_hp"]
                    lines.append(f"{log_prefix} Water flow: water HP up.")
                elif val == "air":
                    for u in team:
                        if u["element"] == "air":
                            u["speed"] = int(u["speed"] * 1.12)
                    lines.append(f"{log_prefix} Air current: air speed up.")
                elif val == "earth":
                    for u in team:
                        if u["element"] == "earth":
                            u["def"] = int(u["def"] * 1.12)
                    lines.append(f"{log_prefix} Earth wall: earth defense up.")
                elif val == "dark":
                    for u in team:
                        if u["element"] == "dark":
                            u["crit"] = min(0.6, u["crit"] + 0.06)
                    lines.append(f"{log_prefix} Dark pact: dark crit up.")
                elif val == "mystic":
                    for u in team:
                        if u["element"] == "mystic":
                            u["status_resist"] += 0.1
                    lines.append(f"{log_prefix} Mystic veil: mystic resist up.")
            elif kind == "role":
                if val == "tank":
                    for u in team:
                        if u["role"] == "tank":
                            u["shield"] += int(u["max_hp"] * 0.12)
                    lines.append(f"{log_prefix} Tank line: bonus shields.")
                elif val == "striker":
                    for u in team:
                        if u["role"] == "striker":
                            u["atk_mod"] *= 1.10
                    lines.append(f"{log_prefix} Striker squad: attack raised.")
                elif val == "support":
                    for u in team:
                        if u["role"] == "support":
                            u["spd_mod"] *= 1.10
                    lines.append(f"{log_prefix} Support chorus: speed up.")
                elif val == "healer":
                    for u in team:
                        if u["role"] == "healer":
                            u["def_mod"] *= 1.08
                    lines.append(f"{log_prefix} Healer circle: safer heals.")
                elif val == "trickster":
                    for u in team:
                        if u["role"] == "trickster":
                            u["crit"] = min(0.6, u["crit"] + 0.05)
                    lines.append(f"{log_prefix} Trickster band: more crits.")
            elif kind == "rarity":
                if val == "Epic":
                    for u in team:
                        if u["rarity"] == "Epic":
                            u["max_hp"] = int(u["max_hp"] * 1.06)
                            u["hp"] = u["max_hp"]
                    lines.append(f"{log_prefix} Epic bond: HP up.")
                elif val == "Legendary":
                    for u in team:
                        if u["rarity"] == "Legendary":
                            u["atk_mod"] *= 1.08
                            u["def_mod"] *= 1.08
                    lines.append(f"{log_prefix} Legendary bond: all stats up.")
        return lines

    def type_multiplier(self, move_elem, target_elem):
        if move_elem is None or target_elem is None:
            base = 1.0
        else:
            base = self.TYPE_CHART.get((move_elem, target_elem), 1.0)
        env_name, env_boost, env_nerf = self.current_env
        if move_elem == env_boost:
            base *= 1.15
        elif move_elem == env_nerf:
            base *= 0.9
        mut = self.world.get("mutator")
        if mut and mut[0] == "Bloodsport":
            base *= 1.1
        elif mut and mut[0] == "Blessed Grounds":
            base *= 0.95
        return base

    def get_moves_for(self, unit):
        el = unit.get("element", "beast")
        return self.MOVE_SETS.get(el, self.MOVE_SETS["beast"])

    def pick_target(self, team):
        alive = [u for u in team if u["hp"] > 0]
        if not alive:
            return None
        mode = random.random()
        if mode < 0.55:
            return min(alive, key=lambda u: u["hp"])
        else:
            return max(alive, key=lambda u: u["power"])

    def apply_on_damage_taken_passive(self, defender, attacker, dmg, log):
        aid = defender["ability_id"]
        if defender.get("clutch") and not defender.get("clutch_used") and defender["hp"] / defender["max_hp"] < 0.2:
            defender["atk_mod"] *= 1.15
            defender["spd_mod"] *= 1.20
            defender["crit"] = min(0.6, defender["crit"] + 0.15)
            defender["clutch_used"] = True
            log.append(f"{defender['name']}'s survival instinct triggers!")
        if aid == "berserker":
            if defender["hp"] / defender["max_hp"] < 0.4:
                defender["atk_mod"] *= 1.10
                log.append(f"{defender['name']}'s Berserker rage boosts its attack!")
        if aid == "hex":
            if random.random() < 0.2 and attacker["hp"] > 0:
                st = random.choice(["bleed", "poison", "stun"])
                attacker["status"] = st
                attacker["status_timer"] = 2
                log.append(f"{defender['name']}'s chaotic hex curses {attacker['name']}!")
        if aid == "bulwark":
            if not defender.get("bulwark_used") and dmg > defender["max_hp"] * 0.35:
                defender["bulwark_used"] = True
                shield = int(defender["max_hp"] * 0.25)
                defender["shield"] += shield
                log.append(f"{defender['name']}'s Titanic Bulwark conjures a shield!")

    def apply_on_attack_passive(self, attacker, defender, dmg, log):
        aid = attacker["ability_id"]
        if aid == "pack_hunter":
            if random.random() < 0.25:
                log.append(f"{attacker['name']} tears in with pack fury!")
        if aid == "finisher":
            if defender["hp"] / defender["max_hp"] < 0.35 and random.random() < 0.3:
                extra = max(1, int(defender["max_hp"] * 0.08))
                defender["hp"] -= extra
                log.append(f"{attacker['name']}'s Executioner strike tears extra {extra} HP!")
        if aid == "scales":
            if random.random() < 0.2:
                attacker["def_mod"] *= 1.12
                log.append(f"{attacker['name']}'s scales harden! Defense rises.")

    def apply_round_end_passives(self, pteam, oteam, log):
        mut = self.world.get("mutator")
        for team in (pteam, oteam):
            alive = [u for u in team if u["hp"] > 0]
            if not alive:
                continue
            healers = [u for u in alive if u["ability_id"] in ("healer", "aura_heal")]
            if healers:
                healer = random.choice(healers)
                target = min(alive, key=lambda u: u["hp"] / u["max_hp"])
                if target["hp"] <= 0:
                    continue
                base_pct = 0.05 if healer["ability_id"] == "healer" else 0.08
                if mut and mut[0] == "Blessed Grounds":
                    base_pct *= 1.3
                if mut and mut[0] == "Bloodsport":
                    base_pct *= 0.7
                amount = max(1, int(target["max_hp"] * base_pct))
                target["hp"] = min(target["max_hp"], target["hp"] + amount)
                log.append(f"{healer['name']}'s aura mends {target['name']} (+{amount} HP)!")
            for u in alive:
                if u["ability_id"] == "speed_aura":
                    for ally in alive:
                        ally["spd_mod"] *= 1.02

    def try_rebirth(self, unit, log):
        if unit["ability_id"] != "rebirth":
            return False
        if unit["has_rebirthed"]:
            return False
        unit["has_rebirthed"] = True
        unit["hp"] = max(1, int(unit["max_hp"] * 0.4))
        log.append(f"{unit['name']} is engulfed in flames and rises again!")
        return True

    def charge_ult(self, unit, amount):
        unit["ult_charge"] = min(100, unit["ult_charge"] + amount)
        if unit["ult_charge"] >= 100:
            unit["ult_ready"] = True

    def reset_ult(self, unit):
        unit["ult_charge"] = 0
        unit["ult_ready"] = False

    def pick_ultimate_name(self, unit):
        el = unit["element"]
        if el == "fire":
            return "Inferno Collapse"
        if el == "water":
            return "Tidal Rebirth"
        if el == "air":
            return "Tempest Assault"
        if el == "earth":
            return "Worldbreaker Slam"
        if el == "dark":
            return "Eclipse Devour"
        if el == "mystic":
            return "Celestial Judgment"
        return "Primal Frenzy"

    def perform_ultimate(self, unit, allies, enemies, log):
        el = unit["element"]
        title = self.pick_ultimate_name(unit)
        lines = [f"{unit['name']} unleashes {title}!"]
        if el == "fire":
            for e in enemies:
                if e["hp"] <= 0:
                    continue
                dmg = max(1, int(e["max_hp"] * 0.2))
                e["hp"] -= dmg
                e["status"] = "burn"
                e["status_timer"] = 3
            lines.append("Flames engulf the enemy team!")
        elif el == "water":
            for a in allies:
                if a["hp"] <= 0:
                    continue
                heal = max(1, int(a["max_hp"] * 0.18))
                a["hp"] = min(a["max_hp"], a["hp"] + heal)
            lines.append("A tidal wave restores your team!")
        elif el == "air":
            for a in allies:
                a["spd_mod"] *= 1.3
                a["atk_mod"] *= 1.1
            lines.append("Hurricane winds accelerate your squad!")
        elif el == "earth":
            for a in allies:
                shield = int(a["max_hp"] * 0.25)
                a["shield"] += shield
            lines.append("The ground rises to shield your fighters!")
        elif el == "dark":
            for e in enemies:
                if e["hp"] <= 0:
                    continue
                dmg = max(1, int(e["max_hp"] * 0.16))
                e["hp"] -= dmg
                e["status"] = "poison"
                e["status_timer"] = 3
            lines.append("Shadows devour enemy vitality!")
        elif el == "mystic":
            target = None
            for e in enemies:
                if e["hp"] > 0:
                    target = e
                    break
            if target:
                dmg = max(1, int(target["max_hp"] * 0.35))
                target["hp"] -= dmg
                lines.append(f"Starfire smites {target['name']} for {dmg} damage!")
        else:
            for e in enemies:
                if e["hp"] <= 0:
                    continue
                dmg = max(1, int(e["max_hp"] * 0.15))
                e["hp"] -= dmg
            lines.append("Primal rage tears through the enemy!")
        self.reset_ult(unit)
        log.extend(lines)
        self.arena["last_ult"] = f"{unit['name']} used {title}"

    async def simulate_battle(self, inter, pteam, oteam):
        log = []
        mut = random.choice(ARENA_MUTATORS)
        self.world["mutator"] = mut
        self.arena["last_mutator"] = mut[0]
        p_sy = self.analyze_synergies(pteam)
        o_sy = self.analyze_synergies(oteam)
        log.extend(self.apply_synergies_to_team(pteam, p_sy, "Your"))
        log.extend(self.apply_synergies_to_team(oteam, o_sy, "Enemy"))
        for team in (pteam, oteam):
            for u in team:
                if u["ability_id"] in ("guard", "bulwark"):
                    shield = int(u["max_hp"] * 0.15)
                    u["shield"] += shield
                    log.append(f"{u['name']}'s {u['ability_name']} grants a {shield} HP shield!")
        await inter.edit_original_response(content="```The crowd roars... The match begins!```")
        await asyncio.sleep(0.5)
        round_no = 1
        while True:
            if all(u["hp"] <= 0 for u in pteam):
                return "loss", log
            if all(u["hp"] <= 0 for u in oteam):
                return "win", log
            if round_no > 60:
                return "draw", log
            acting = []
            for u in pteam + oteam:
                if u["hp"] > 0:
                    effective_speed = u["speed"] * u["spd_mod"] + random.uniform(0, 5)
                    acting.append((effective_speed, u))
            acting.sort(key=lambda x: x[0], reverse=True)
            for _, unit in acting:
                if unit["hp"] <= 0:
                    continue
                side = "p" if unit in pteam else "o"
                allies = pteam if side == "p" else oteam
                enemies = oteam if side == "p" else pteam
                if all(u["hp"] <= 0 for u in enemies):
                    break
                target = self.pick_target(enemies)
                if not target:
                    continue
                if unit["ult_ready"]:
                    title = self.pick_ultimate_name(unit)
                    attacker, defender = (unit, target) if side == "p" else (target, unit)
                    await self.play_ultimate_animation(
                        inter,
                        attacker,
                        defender,
                        side,
                        [f"{unit['name']} — ULTIMATE", title.upper()]
                    )
                    self.perform_ultimate(unit, allies, enemies, log)
                    continue
                moves = self.get_moves_for(unit)
                move = random.choice(moves)
                text_lines = [f"Round {round_no}", f"{unit['name']} used {move['name']}!"]
                if unit["status"] == "stun":
                    text_lines = [f"Round {round_no}", f"{unit['name']} is stunned and cannot move!"]
                    unit["status"] = None
                    unit["status_timer"] = 0
                    log.extend(text_lines)
                    attacker, defender = (unit, target) if side == "p" else (target, unit)
                    await self.play_attack_animation(inter, attacker, defender, side, "\n".join(text_lines))
                    self.charge_ult(unit, 5)
                    continue
                if move["kind"] == "buff":
                    if move["status"] == "atk_up":
                        unit["atk_mod"] *= 1.25
                        text_lines.append(f"{unit['name']}'s power rose!")
                    elif move["status"] == "def_up":
                        unit["def_mod"] *= 1.25
                        text_lines.append(f"{unit['name']}'s defense rose!")
                    elif move["status"] == "spd_up":
                        unit["spd_mod"] *= 1.25
                        text_lines.append(f"{unit['name']}'s speed rose!")
                    elif move["status"] == "regen":
                        unit["status"] = "regen"
                        unit["status_timer"] = 3
                        text_lines.append(f"{unit['name']} is surrounded by healing energy!")
                    log.extend(text_lines)
                    attacker, defender = (unit, target) if side == "p" else (target, unit)
                    await self.play_attack_animation(inter, attacker, defender, side, "\n".join(text_lines))
                    self.charge_ult(unit, 15)
                    continue
                if random.random() > move["accuracy"]:
                    text_lines.append("But it missed!")
                    log.extend(text_lines)
                    attacker, defender = (unit, target) if side == "p" else (target, unit)
                    await self.play_attack_animation(inter, attacker, defender, side, "\n".join(text_lines))
                    self.charge_ult(unit, 10)
                    continue
                hits = 1
                if "Claw" in move["name"] or "Fang" in move["name"]:
                    hits = 2 if random.random() < 0.2 else 1
                total_dmg = 0
                mut = self.world.get("mutator")
                for _ in range(hits):
                    base = unit["power"] * unit["atk_mod"] - target["def"] * target["def_mod"]
                    if base < 5:
                        base = 5
                    crit = False
                    if random.random() < unit["crit"]:
                        crit = True
                        base *= 1.7
                    if random.random() < 0.3:
                        unit["atk_mod"] *= 1.12
                        log.append(f"{unit['name']} surges with momentum!")
                    stab = 1.2 if move["element"] == unit["element"] else 1.0
                    type_mult = self.type_multiplier(move["element"], target["element"])
                    dmg = int(base * move["power"] * stab * type_mult * random.uniform(0.85, 1.0))
                    if mut and mut[0] == "Bloodsport":
                        dmg = int(dmg * 1.15)
                    if mut and mut[0] == "Iron Wall":
                        dmg = int(dmg * 0.9)
                    if dmg < 1:
                        dmg = 1
                    if target["shield"] > 0:
                        absorbed = min(target["shield"], dmg)
                        target["shield"] -= absorbed
                        dmg -= absorbed
                        if absorbed > 0:
                            text_lines.append(f"{target['name']}'s shield absorbs {absorbed} damage!")
                    target["hp"] -= dmg
                    total_dmg += dmg
                    eff_text = ""
                    if type_mult > 1.25:
                        eff_text = "It's super effective!"
                    elif type_mult < 0.9:
                        eff_text = "It's not very effective..."
                    text_lines.append(f"Hit for {dmg} damage.")
                    if crit:
                        text_lines.append("A critical hit!")
                    if eff_text:
                        text_lines.append(eff_text)
                    if target["hp"] <= 0:
                        if not self.try_rebirth(target, text_lines):
                            target["hp"] = 0
                            text_lines.append(f"{target['name']} has fallen!")
                        break
                if unit["role"] == "striker" and total_dmg > 0 and unit["hp"] > 0:
                    ls = int(total_dmg * 0.1)
                    unit["hp"] = min(unit["max_hp"], unit["hp"] + ls)
                    text_lines.append(f"{unit['name']} siphons {ls} HP from the assault!")
                if move["status"] in ("burn", "poison", "bleed", "stun") and target["hp"] > 0:
                    mut = self.world.get("mutator")
                    status_mult = 1.0
                    if mut and mut[0] == "Arcane Storm":
                        status_mult = 1.25
                    if random.random() < move["status_chance"] * (1.0 - target["status_resist"]) * status_mult:
                        target["status"] = move["status"]
                        if move["status"] == "burn":
                            target["status_timer"] = 3
                            text_lines.append(f"{target['name']} was burned!")
                        elif move["status"] == "poison":
                            target["status_timer"] = 4
                            text_lines.append(f"{target['name']} was poisoned!")
                        elif move["status"] == "bleed":
                            target["status_timer"] = 3
                            text_lines.append(f"{target['name']} is bleeding!")
                        elif move["status"] == "stun":
                            target["status_timer"] = 1
                            text_lines.append(f"{target['name']} was stunned!")
                self.apply_on_attack_passive(unit, target, total_dmg, text_lines)
                self.apply_on_damage_taken_passive(target, unit, total_dmg, text_lines)
                self.charge_ult(unit, 18)
                self.charge_ult(target, 12)
                log.extend(text_lines)
                attacker, defender = (unit, target) if side == "p" else (target, unit)
                await self.play_attack_animation(inter, attacker, defender, side, "\n".join(text_lines))
                if all(u["hp"] <= 0 for u in pteam):
                    return "loss", log
                if all(u["hp"] <= 0 for u in oteam):
                    return "win", log
            mut = self.world.get("mutator")
            for team in (pteam, oteam):
                for unit in team:
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
                            if mut and mut[0] == "Blessed Grounds":
                                heal = int(heal * 1.3)
                            unit["hp"] = min(unit["max_hp"], unit["hp"] + heal)
                            log.append(f"{unit['name']} regains {heal} HP!")
                        unit["status_timer"] -= 1
                        if unit["status_timer"] <= 0:
                            unit["status"] = None
            if self.world.get("mutator") and self.world["mutator"][0] == "Chaotic Whirl":
                for team in (pteam, oteam):
                    for u in team:
                        if u["hp"] <= 0:
                            continue
                        u["atk_mod"] *= random.uniform(0.85, 1.20)
                        u["def_mod"] *= random.uniform(0.85, 1.20)
                        u["spd_mod"] *= random.uniform(0.85, 1.20)
                        if random.random() < 0.1:
                            u["ult_charge"] = min(100, u["ult_charge"] + random.randint(20, 40))
                        if random.random() < 0.15:
                            u["status"] = random.choice(["burn", "poison", "bleed", "stun", None])
                            u["status_timer"] = random.randint(1, 3) if u["status"] else 0
                        if random.random() < 0.1:
                            u["atk_mod"], u["def_mod"] = u["def_mod"], u["atk_mod"]
                        if random.random() < 0.06 and team:
                            t = random.choice(team)
                            if t["hp"] > 0 and t != u:
                                u["spd_mod"], t["spd_mod"] = t["spd_mod"], u["spd_mod"]
            self.apply_round_end_passives(pteam, oteam, log)
            round_no += 1

    async def start_match(self, inter):
        self.arena["tokens"] -= 1
        self.arena["in_battle"] = True
        player_team = list(self.arena["loadout"])
        if not player_team:
            self.arena["tokens"] += 1
            return await inter.response.send_message("You have no team selected.", ephemeral=True)
        opponent_team = random.sample(list(ASCII_SPRITES.keys()), k=min(5, len(ASCII_SPRITES)))
        self.arena["last_opponent"] = opponent_team
        pstats = self.build_team_stats([{"name": x} for x in player_team], is_player=True)
        ostats = self.build_team_stats([{"name": x} for x in opponent_team], is_player=False)
        await inter.response.send_message(content="```Battle starting...```")
        result, log = await self.simulate_battle(inter, pstats, ostats)
        await self.process_match_result(inter, result, log, opponent_team)

    async def process_match_result(self, inter, result, log, opponent):
        rating = self.arena["rating"]
        xp = self.arena["xp"]
        level = self.arena["level"]
        streak = self.arena["streak"]
        if result == "win":
            delta = random.randint(20, 35)
            xp_gain = random.randint(35, 60)
            crowns = random.randint(0, 3)
            rating += delta
            xp += xp_gain
            streak += 1
            self.arena["wins"] += 1
            self.arena["crowns"] += crowns
            self.world["chaos"] += 0.05
            if self.arena["tokens"] < 5:
                self.arena["tokens"] += 1
            res = (
                f"Victory!\n"
                f"Rating +{delta}\n"
                f"XP +{xp_gain}\n"
                f"Crowns +{crowns}\n"
                f"+1 Fight Token"
            )
        elif result == "loss":
            delta = -random.randint(8, 20)
            xp_gain = random.randint(15, 30)
            rating += delta
            xp += xp_gain
            streak = 0
            self.arena["losses"] += 1
            self.world["chaos"] += 0.02
            res = (
                f"Defeat.\n"
                f"Rating {delta}\n"
                f"XP +{xp_gain}"
            )
        else:
            xp_gain = random.randint(10, 18)
            xp += xp_gain
            self.world["chaos"] += 0.01
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
        self.world["total_matches"] += 1
        evolution_text = ""
        if result == "win" and streak >= 3:
            if self.arena["loadout"]:
                candidate_name = random.choice(self.arena["loadout"])
                evo_target = EVOLUTIONS.get(candidate_name)
                if evo_target:
                    self.arena["evolved"][candidate_name] = evo_target
                    self.arena["loadout"] = [self.arena["evolved"].get(n, n) for n in self.arena["loadout"]]
                    evolution_text = f"\n\n✨ Evolution! {candidate_name} has awakened into **{evo_target}**!"
        if self.world["chaos"] > 6:
            self.world["season"] += 1
            self.world["chaos"] = 0
            self.world["last_event"] = "A new Arena Season begins! The rules feel different."
            self.current_env = self.pick_environment()
        self.arena["last_log"] = res + evolution_text
        save_state()
        battle_text = "\n".join(log[-25:])
        opp_text = ", ".join(opponent)
        mut = self.world.get("mutator")
        mut_name = mut[0] if mut else "None"
        embed = discord.Embed(
            title="🏟️ ARENA MATCH RESULT",
            description=(
                f"Result: **{result.upper()}**\n"
                f"Opponent Team: {opp_text}\n"
                f"Mutator: **{mut_name}**\n\n"
                f"{res}{evolution_text}\n\n"
                f"__Battle Log (Last 25 events):__\n{battle_text}"
            ),
            color=discord.Color.gold()
        )
        await inter.edit_original_response(content=None, embed=embed)

    async def edit_team(self, inter):
        if not self.owned:
            return await inter.response.send_message("You own no animals.", ephemeral=True)
        options = []
        for i, pet in enumerate(self.owned):
            nm = self.pet_name(pet)
            el = self.infer_element(nm)
            role, rarity, _ = self.assign_role_rarity(nm)
            options.append(discord.SelectOption(label=nm, value=f"{nm}:{i}", description=f"{rarity} {role}, {el}"))
        select = discord.ui.Select(
            placeholder="Select up to 5 animals for your Arena team",
            min_values=1,
            max_values=min(5, len(options)),
            options=options
        )
        async def select_callback(sel_inter):
            if sel_inter.user.id != self.uid:
                return await sel_inter.response.send_message("Not your Arena.", ephemeral=True)
            chosen = [v.split(":", 1)[0] for v in select.values]
            self.arena["loadout"] = chosen
            self.arena["last_log"] = f"Team updated: {', '.join(chosen)}"
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
            except Exception:
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
        await inter.edit_original_response(embed=embed, view=v)

    async def crown_shop(self, inter):
        items = {
            "might": {"name": "Might Emblem", "cost": 3, "key": "power_boost", "amount": 0.05},
            "haste": {"name": "Haste Emblem", "cost": 3, "key": "speed_boost", "amount": 0.07},
            "ward": {"name": "Ward Emblem", "cost": 3, "key": "def_boost", "amount": 0.07},
            "luck": {"name": "Lucky Emblem", "cost": 4, "key": "crit_boost", "amount": 0.03},
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
            await sel_inter.edit_original_response(embed=self.render_lobby(), view=self)
        select.callback = select_callback
        v = discord.ui.View(timeout=180)
        v.add_item(select)
        embed = discord.Embed(
            title="🎖️ Arena Crown Shop",
            description=f"You have **{self.arena['crowns']}** crowns.\nChoose a permanent Arena buff to purchase.",
            color=discord.Color.orange()
        )
        async def back_callback(bi):
            if bi.user.id != self.uid:
                return await bi.response.send_message("Not your Arena.", ephemeral=True)
            await bi.edit_original_response(embed=self.render_lobby(), view=self)

        back_btn = discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary)
        back_btn.callback = back_callback
        v.add_item(back_btn)
        await inter.response.edit_message(embed=embed, view=v)


async def setup(bot):
    await bot.add_cog(HorseyArena(bot))
