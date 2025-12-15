import discord
from discord.ext import commands
from discord import app_commands
import time
import re
import json
import os
import datetime
from collections import defaultdict, deque
from typing import Optional

AUTOMOD_FILE = "automod_config.json"
OFFENCES_FILE = "automod_offences.json"
TEST_USER_IDS: set[int] = set()
AUTOMOD_BLOCKED_MESSAGES: set[int] = set()

def alog(*args):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[AUTOMOD {ts}]", *args)

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

AUTOMOD_DATA = _load_json(AUTOMOD_FILE, {})

def load_offences():
    raw = _load_json(OFFENCES_FILE, {})
    out: dict[int, dict[int, int]] = {}
    try:
        for gid, users in raw.items():
            g = int(gid)
            out[g] = {}
            for uid, v in users.items():
                out[g][int(uid)] = int(v)
    except:
        return {}
    return out

def save_offences(offences: dict[int, dict[int, int]]):
    _save_json(OFFENCES_FILE, {str(g): {str(u): v for u, v in users.items()} for g, users in offences.items()})

def save_automod():
    _save_json(AUTOMOD_FILE, AUTOMOD_DATA)

def censor_word(w: str) -> str:
    if not w:
        return ""
    if len(w) <= 3:
        return w[0] + "*" * (len(w) - 1)
    return w[:-3] + "***"

def has_mod_perms(member: discord.Member) -> bool:
    if member.id in TEST_USER_IDS:
        return False
    gp = member.guild_permissions
    return gp.manage_messages or gp.administrator or member == member.guild.owner

_invite_re = re.compile(r"(?:discord\.gg|discord(?:app)?\.com\/invite)\/[A-Za-z0-9\-]+", re.I)
_url_re = re.compile(r"https?:\/\/\S+|www\.\S+", re.I)
_zalgo_re = re.compile(r"[\u0300-\u036f\u0483-\u0489\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7-\u06e8\u06ea-\u06ed]+")
_ws_re = re.compile(r"\s+")
_non_alnum_space_re = re.compile(r"[^a-z0-9\s]")
_repeat_re = re.compile(r"(.)\1{2,}")

class AutoModEngine:
    def __init__(self):
        self.msg_times = defaultdict(lambda: deque(maxlen=64))
        self.msg_norms = defaultdict(lambda: deque(maxlen=16))
        self.offences = defaultdict(lambda: defaultdict(int))
        self.last_punish = defaultdict(float)
        loaded = load_offences()
        for gid, users in loaded.items():
            for uid, v in users.items():
                self.offences[gid][uid] = v

    def get_cfg(self, guild_id: int) -> dict:
        gid = str(guild_id)
        if gid not in AUTOMOD_DATA:
            AUTOMOD_DATA[gid] = {}
        cfg = AUTOMOD_DATA[gid]

        cfg.setdefault("enabled", False)
        cfg.setdefault("slurs", [])
        cfg.setdefault("punishments", {"1": "warn", "2": "timeout:5", "3": "kick", "4": "ban"})
        cfg.setdefault("delete", True)
        cfg.setdefault("log", False)
        cfg.setdefault("cooldown_seconds", 10)

        cfg.setdefault("spam", {})
        spam = cfg["spam"]
        spam.setdefault("window_seconds", 6)
        spam.setdefault("max_messages", 5)
        spam.setdefault("duplicate_count", 3)
        spam.setdefault("max_mentions", 6)
        spam.setdefault("max_links", 4)
        spam.setdefault("caps_ratio", 0.75)
        spam.setdefault("caps_min_len", 12)
        spam.setdefault("max_zalgo_marks", 12)
        spam.setdefault("repeat_char_limit", 8)

        cfg.setdefault("filters", {})
        flt = cfg["filters"]
        flt.setdefault("block_invites", False)
        flt.setdefault("block_links", False)

        save_automod()
        return cfg

    def normalize(self, text: str) -> str:
        t = text.lower()
        t = _zalgo_re.sub("", t)
        t = _non_alnum_space_re.sub("", t)
        t = _repeat_re.sub(r"\1\1", t)
        t = _ws_re.sub(" ", t).strip()
        return t

    def _count_links(self, content: str) -> int:
        return len(_url_re.findall(content))

    def _count_mentions(self, message: discord.Message) -> int:
        c = len(message.mentions) + len(message.role_mentions)
        if message.mention_everyone:
            c += 10
        return c

    def _caps_ratio(self, content: str) -> float:
        letters = [ch for ch in content if ch.isalpha()]
        if not letters:
            return 0.0
        caps = sum(1 for ch in letters if ch.isupper())
        return caps / max(1, len(letters))

    def _zalgo_marks(self, content: str) -> int:
        return len(_zalgo_re.findall(content))

    def _repeat_char_run(self, content: str) -> int:
        m = re.findall(r"(.)\1+", content)
        if not m:
            return 0
        longest = 0
        cur = 1
        last = ""
        for ch in content:
            if ch == last:
                cur += 1
            else:
                longest = max(longest, cur)
                cur = 1
                last = ch
        longest = max(longest, cur)
        return longest

    def contains_slur(self, text: str, slurs: list[str]) -> Optional[str]:
        lowered = self.normalize(text)
        for s in slurs:
            if not s:
                continue
            pat = rf"\b{re.escape(s.lower())}\b"
            if re.search(pat, lowered):
                return s
        return None

    def _record(self, guild_id: int, user_id: int, norm: str):
        now = time.time()
        key = (guild_id, user_id)
        self.msg_times[key].append(now)
        self.msg_norms[key].append(norm)

    def _rate_spam(self, cfg: dict, guild_id: int, user_id: int) -> bool:
        now = time.time()
        key = (guild_id, user_id)
        window = float(cfg["spam"]["window_seconds"])
        max_msgs = int(cfg["spam"]["max_messages"])
        times = self.msg_times[key]
        recent = 0
        for t in reversed(times):
            if now - t <= window:
                recent += 1
            else:
                break
        return recent >= max_msgs

    def _duplicate_spam(self, cfg: dict, guild_id: int, user_id: int, norm: str) -> bool:
        key = (guild_id, user_id)
        need = int(cfg["spam"]["duplicate_count"])
        norms = self.msg_norms[key]
        return norms.count(norm) >= need

    def _signal_checks(self, cfg: dict, message: discord.Message) -> Optional[str]:
        content = message.content or ""
        if cfg["filters"]["block_invites"] and _invite_re.search(content):
            return "invite link"
        if cfg["filters"]["block_links"] and _url_re.search(content):
            return "link"
        if self._count_mentions(message) >= int(cfg["spam"]["max_mentions"]):
            return "mention spam"
        if self._count_links(content) >= int(cfg["spam"]["max_links"]):
            return "link spam"
        if len(content) >= int(cfg["spam"]["caps_min_len"]) and self._caps_ratio(content) >= float(cfg["spam"]["caps_ratio"]):
            return "excessive caps"
        if self._zalgo_marks(content) >= int(cfg["spam"]["max_zalgo_marks"]):
            return "zalgo / combining marks"
        if self._repeat_char_run(content) >= int(cfg["spam"]["repeat_char_limit"]):
            return "character spam"
        return None

    async def handle_message(self, message: discord.Message) -> bool:
        if not message.guild or message.author.bot:
            return False
        if not isinstance(message.author, discord.Member):
            return False
        if has_mod_perms(message.author):
            return False

        cfg = self.get_cfg(message.guild.id)
        if not cfg.get("enabled", False):
            return False

        content = message.content or ""
        norm = self.normalize(content)
        self._record(message.guild.id, message.author.id, norm)

        if self._rate_spam(cfg, message.guild.id, message.author.id):
            AUTOMOD_BLOCKED_MESSAGES.add(message.id)
            await self.punish(message, "spam (rate)")
            return True

        if norm and self._duplicate_spam(cfg, message.guild.id, message.author.id, norm):
            AUTOMOD_BLOCKED_MESSAGES.add(message.id)
            await self.punish(message, "spam (duplicate)")
            return True

        sig = self._signal_checks(cfg, message)
        if sig:
            AUTOMOD_BLOCKED_MESSAGES.add(message.id)
            await self.punish(message, sig)
            return True

        slur = self.contains_slur(content, cfg.get("slurs", []))
        if slur:
            AUTOMOD_BLOCKED_MESSAGES.add(message.id)
            await self.punish(message, f"slur ({censor_word(slur)})")
            return True

        return False

    async def punish(self, message: discord.Message, reason: str):
        now = time.time()
        guild = message.guild
        user = message.author
        gid = guild.id
        uid = user.id

        cfg = self.get_cfg(gid)
        cd = float(cfg.get("cooldown_seconds", 10))
        last = self.last_punish.get((gid, uid), 0.0)
        if now - last < cd:
            return
        self.last_punish[(gid, uid)] = now

        self.offences[gid][uid] += 1
        level = int(self.offences[gid][uid])
        save_offences({g: dict(users) for g, users in self.offences.items()})

        action = cfg.get("punishments", {}).get(str(level))
        alog("PUNISH", f"guild={gid}", f"user={uid}", f"level={level}", f"action={action}", f"reason={reason}")

        if cfg.get("delete", True):
            try:
                await message.delete()
            except:
                pass

        if not action:
            return

        if action == "warn":
            try:
                await message.channel.send(f"{user.mention} warning: stop ({reason}).")
            except:
                pass
            return

        if action.startswith("timeout:"):
            try:
                minutes = int(action.split(":", 1)[1])
            except:
                minutes = 5
            try:
                await user.timeout(datetime.timedelta(minutes=minutes), reason=f"automod: {reason}")
            except:
                pass
            try:
                await message.channel.send(f"{user.mention} muted for {minutes} minutes. reason: {reason}.")
            except:
                pass
            return

        if action == "kick":
            try:
                await guild.kick(user, reason=f"automod: {reason}")
            except:
                return
            try:
                await message.channel.send(f"🚪 **{user} was kicked** due to **{reason}**.")
            except:
                pass
            return

        if action == "ban":
            try:
                await guild.ban(user, reason=f"automod: {reason}", delete_message_days=0)
            except:
                return
            try:
                await message.channel.send(f"🔨 **{user} was banned** due to **{reason}**.")
            except:
                pass
            return

ENGINE = AutoModEngine()

class AutoModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.engine = ENGINE

    @app_commands.command(name="automod", description="Enable or disable automod")
    @app_commands.describe(mode="on or off")
    async def automod(self, interaction: discord.Interaction, mode: str):
        if not interaction.guild:
            return await interaction.response.send_message("guild only", ephemeral=True)
        if not isinstance(interaction.user, discord.Member) or not has_mod_perms(interaction.user):
            return await interaction.response.send_message("you dont have permission to do that", ephemeral=True)
        cfg = self.engine.get_cfg(interaction.guild.id)
        cfg["enabled"] = (mode or "").lower() == "on"
        save_automod()
        await interaction.response.send_message(f"automod {'enabled' if cfg['enabled'] else 'disabled'}")

    @app_commands.command(name="automod_reset", description="Reset automod offence points for a user")
    @app_commands.describe(user="User to reset automod points for")
    async def automod_reset(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.guild:
            return await interaction.response.send_message("guild only", ephemeral=True)
        if not isinstance(interaction.user, discord.Member) or not has_mod_perms(interaction.user):
            return await interaction.response.send_message("you dont have permission to do that", ephemeral=True)

        gid = interaction.guild.id
        uid = user.id

        if gid in self.engine.offences and uid in self.engine.offences[gid]:
            self.engine.offences[gid][uid] = 0
            save_offences({g: dict(users) for g, users in self.engine.offences.items()})
            msg = f"🔄 automod points reset for **{user}**."
        else:
            msg = f"ℹ️ **{user}** had no automod points."
        await interaction.response.send_message(msg)

    @app_commands.command(name="automod_punishment", description="Set automod punishment for an offence level")
    @app_commands.describe(level="Offence number (1, 2, 3, ...)", action="warn | timeout:minutes | kick | ban")
    async def automod_punishment(self, interaction: discord.Interaction, level: int, action: str):
        if not interaction.guild:
            return await interaction.response.send_message("guild only", ephemeral=True)
        if not isinstance(interaction.user, discord.Member) or not has_mod_perms(interaction.user):
            return await interaction.response.send_message("you dont have permission to do that", ephemeral=True)
        if level < 1:
            return await interaction.response.send_message("level must be >= 1", ephemeral=True)

        action = (action or "").lower().strip()
        valid = action in {"warn", "kick", "ban"} or (action.startswith("timeout:") and action.split(":", 1)[1].isdigit())
        if not valid:
            return await interaction.response.send_message("invalid action. use warn, kick, ban, or timeout:<minutes>", ephemeral=True)

        cfg = self.engine.get_cfg(interaction.guild.id)
        cfg["punishments"][str(level)] = action
        save_automod()
        await interaction.response.send_message(f"✅ automod punishment set: level {level} → `{action}`")

    @app_commands.command(name="automod_slurs", description="Manage automod slurs")
    @app_commands.describe(action="list, add, or remove", word="word for add/remove")
    async def automod_slurs(self, interaction: discord.Interaction, action: str, word: Optional[str] = None):
        if not interaction.guild:
            return await interaction.response.send_message("guild only", ephemeral=True)
        if not isinstance(interaction.user, discord.Member) or not has_mod_perms(interaction.user):
            return await interaction.response.send_message("you dont have permission to do that", ephemeral=True)

        cfg = self.engine.get_cfg(interaction.guild.id)
        action = (action or "").lower().strip()

        if action == "list":
            if not cfg["slurs"]:
                return await interaction.response.send_message("no slurs set")
            lines = [censor_word(w) for w in cfg["slurs"]]
            return await interaction.response.send_message("**automod slurs:**\n" + ", ".join(lines))

        if action == "add":
            if not word:
                return await interaction.response.send_message("give a word", ephemeral=True)
            w = word.lower().strip()
            if not w:
                return await interaction.response.send_message("give a word", ephemeral=True)
            if w in cfg["slurs"]:
                return await interaction.response.send_message("already exists", ephemeral=True)
            cfg["slurs"].append(w)
            save_automod()
            return await interaction.response.send_message(f"added `{censor_word(w)}`")

        if action == "remove":
            if not word:
                return await interaction.response.send_message("give a word", ephemeral=True)
            w = word.lower().strip()
            if w not in cfg["slurs"]:
                return await interaction.response.send_message("not found", ephemeral=True)
            cfg["slurs"].remove(w)
            save_automod()
            return await interaction.response.send_message(f"removed `{censor_word(w)}`")

        await interaction.response.send_message("actions: list, add, remove", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoModCog(bot))
