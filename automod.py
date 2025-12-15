import discord
from discord.ext import commands
from discord import app_commands
import time
import re
import json
import os
import datetime
from collections import defaultdict, deque

AUTOMOD_FILE = "automod_config.json"
OFFENCES_FILE = "automod_offences.json"
TEST_USER_IDS = {1238242784679563265}
AUTOMOD_BLOCKED_MESSAGES: set[int] = set()

WINDOW = 5
COUNT = 4

def alog(*args):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[AUTOMOD {ts}]", *args)

def load_automod():
    if not os.path.exists(AUTOMOD_FILE):
        return {}
    try:
        with open(AUTOMOD_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_automod(data):
    with open(AUTOMOD_FILE, "w") as f:
        json.dump(data, f, indent=2)

AUTOMOD_DATA = load_automod()

def load_offences():
    if not os.path.exists(OFFENCES_FILE):
        return {}
    try:
        with open(OFFENCES_FILE, "r") as f:
            data = json.load(f)
            return {
                int(gid): {int(uid): int(v) for uid, v in users.items()}
                for gid, users in data.items()
            }
    except Exception as e:
        print("[AUTOMOD] failed to load offences:", e)
        return {}

def save_offences(data):
    with open(OFFENCES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def censor_word(w: str) -> str:
    if len(w) <= 3:
        return w[0] + "*" * (len(w) - 1)
    return w[:-3] + "***"

def has_mod_perms(member: discord.Member) -> bool:
    if member.id in TEST_USER_IDS:
        return False
    return (
        member.guild_permissions.manage_messages
        or member.guild_permissions.administrator
        or member == member.guild.owner
    )


class AutoModEngine:
    def __init__(self):
        self.last_messages = defaultdict(lambda: deque(maxlen=5))
        self.msg_times = defaultdict(lambda: deque(maxlen=10))
        self.offences = defaultdict(lambda: defaultdict(int))
        self.last_punish = defaultdict(float)
        loaded = load_offences()
        self.offences = defaultdict(lambda: defaultdict(int))

        for gid, users in loaded.items():
            for uid, value in users.items():
                self.offences[gid][uid] = value

    def get_cfg(self, guild_id: int):
        gid = str(guild_id)
    
        if gid not in AUTOMOD_DATA:
            AUTOMOD_DATA[gid] = {}
    
        cfg = AUTOMOD_DATA[gid]
    
        cfg.setdefault("enabled", False)
        cfg.setdefault("slurs", [])
        cfg.setdefault("punishments", {
            "1": "warn",
            "2": "timeout:5",
            "3": "kick",
            "4": "ban"
        })
    
        save_automod(AUTOMOD_DATA)
        return cfg


    def record_message(self, guild_id: int, user_id: int):
        now = time.time()
        self.msg_times[(guild_id, user_id)].append(now)
        
    def is_spam(self, guild_id: int, user_id: int, content: str) -> bool:
        now = time.time()
    
        times = self.msg_times[(guild_id, user_id)]
        recent = [t for t in times if now - t <= WINDOW]
    
        alog(
            "CHECK-SPAM",
            f"user={user_id}",
            f"recent_msgs={len(recent)}",
            f"window={WINDOW}",
            f"count={COUNT}",
        )
    
        if len(recent) >= COUNT:
            alog("SPAM-HIT", f"user={user_id}", "reason=rate")
            return True
    
        msgs = self.last_messages[(guild_id, user_id)]
        norm = self.normalize(content)
        msgs.append(norm)
    
        if msgs.count(norm) >= 3:
            alog("SPAM-HIT", f"user={user_id}", "reason=duplicate")
            return True
    
        return False

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)  
        text = re.sub(r"(.)\1{2,}", r"\1\1", text)
        return text
    
    def contains_slur(self, text: str, slurs: list[str]) -> str | None:
        lowered = self.normalize(text)
        for s in slurs:
            if re.search(rf"\b{re.escape(s)}\b", lowered):
                return s
        return None
        
    async def handle_message(self, message: discord.Message) -> bool:
        if not message.guild or message.author.bot:
            return False
    
        if has_mod_perms(message.author):
            return False
        alog(
            "MSG",
            f"guild={message.guild.id}",
            f"user={message.author.id}",
            f"content={message.content!r}"
        )

        cfg = self.get_cfg(message.guild.id)
        if not cfg["enabled"]:
            return False
    
        self.record_message(message.guild.id, message.author.id)
    
        if self.is_spam(
            message.guild.id,
            message.author.id,
            message.content
        ):
            AUTOMOD_BLOCKED_MESSAGES.add(message.id)
            await self.punish(message, "spam")
            return True 
    
        slur = self.contains_slur(message.content, cfg["slurs"])
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
    
        last = self.last_punish.get((gid, uid), 0)
        if now - last < 10:
            return
    
        self.last_punish[(gid, uid)] = now

        alog(
            "PUNISH",
            f"user={user.id}",
            f"guild={guild.id}",
            f"reason={reason}"
        )
      
        self.offences[gid][uid] += 1
        level = self.offences[gid][uid]

        save_offences({
            str(gid): {str(uid): v for uid, v in users.items()}
            for gid, users in self.offences.items()
        })

  
        cfg = self.get_cfg(gid)
        action = cfg.get("punishments", {}).get(str(level))

        alog(
            "OFFENCE",
            f"user={uid}",
            f"level={level}",
            f"action={action}"
        )
        
        if not action:
            return
    
        if action == "warn":
            await message.channel.send(
                f"{user.mention} warning: stop ({reason})."
            )
    
        elif action.startswith("timeout"):
            minutes = int(action.split(":")[1])
            try:
                await user.timeout(
                    datetime.timedelta(minutes=minutes),
                    reason=f"automod: {reason}"
                )
            except:
                pass
            await message.channel.send(
                f"{user.mention} muted for {minutes} minutes. reason: {reason}."
            )
    
        elif action == "kick":
            await message.channel.send(
                f"🚪 **{user} was kicked** due to **{reason}**."
            )
            try:
                await guild.kick(user, reason=f"automod: {reason}")
            except Exception as e:
                alog("TIMEOUT-FAIL", f"user={uid}", repr(e))

    
        elif action == "ban":
            await message.channel.send(
                f"🔨 **{user} was banned** due to **{reason}**."
            )
            try:
                await guild.ban(user, reason=f"automod: {reason}")
            except Exception as e:
                alog("TIMEOUT-FAIL", f"user={uid}", repr(e))


        try:
            await message.delete()
            alog("DELETE", f"msg={message.id}", "ok")
        except Exception as e:
            alog("DELETE-FAIL", f"msg={message.id}", repr(e))



ENGINE = AutoModEngine()

class AutoModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = ENGINE

    @app_commands.command(name="automod", description="Enable or disable automod")
    @app_commands.describe(mode="on or off")
    async def automod(self, interaction: discord.Interaction, mode: str):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message(
                "you dont have permission to do that", ephemeral=True
            )

        cfg = ENGINE.get_cfg(interaction.guild.id)
        cfg["enabled"] = mode.lower() == "on"
        save_automod(AUTOMOD_DATA)

        await interaction.response.send_message(
            f"automod {'enabled' if cfg['enabled'] else 'disabled'}"
        )

    @app_commands.command(
        name="automod_reset",
        description="Reset automod offence points for a user"
    )
    @app_commands.describe(user="User to reset automod points for")
    async def automod_reset(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message(
                "you dont have permission to do that",
                ephemeral=True
            )

        gid = interaction.guild.id
        uid = user.id

        if gid in ENGINE.offences and uid in ENGINE.offences[gid]:
            ENGINE.offences[gid][uid] = 0
            save_offences({
                str(gid): {str(uid): v for uid, v in users.items()}
                for gid, users in ENGINE.offences.items()
            })
            msg = f"🔄 automod points reset for **{user}**."
        else:
            msg = f"ℹ️ **{user}** had no automod points."

        await interaction.response.send_message(msg)
        
    @app_commands.command(
        name="automod_punishment",
        description="Set automod punishment for an offence level"
    )
    @app_commands.describe(
        level="Offence number (1, 2, 3, ...)",
        action="warn | timeout:minutes | kick | ban"
    )
    async def automod_punishment(
        self,
        interaction: discord.Interaction,
        level: int,
        action: str
    ):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message(
                "you dont have permission to do that",
                ephemeral=True
            )
    
        cfg = ENGINE.get_cfg(interaction.guild.id)
    
        if level < 1:
            return await interaction.response.send_message(
                "level must be >= 1",
                ephemeral=True
            )
    
        action = action.lower()
    
        valid = (
            action == "warn"
            or action == "kick"
            or action == "ban"
            or (action.startswith("timeout:") and action.split(":")[1].isdigit())
        )
    
        if not valid:
            return await interaction.response.send_message(
                "invalid action. use warn, kick, ban, or timeout:<minutes>",
                ephemeral=True
            )
    
        cfg["punishments"][str(level)] = action
        save_automod(AUTOMOD_DATA)
    
        await interaction.response.send_message(
            f"✅ automod punishment set: level {level} → `{action}`"
        )

    
    @app_commands.command(name="automod_slurs", description="Manage automod slurs")
    @app_commands.describe(action="list, add, or remove", word="word for add/remove")
    async def automod_slurs(
        self,
        interaction: discord.Interaction,
        action: str,
        word: str | None = None
    ):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message(
                "you dont have permission to do that", ephemeral=True
            )

        cfg = ENGINE.get_cfg(interaction.guild.id)

        action = action.lower()

        if action == "list":
            if not cfg["slurs"]:
                return await interaction.response.send_message("no slurs set")

            lines = [censor_word(w) for w in cfg["slurs"]]
            await interaction.response.send_message(
                "**automod slurs:**\n" + ", ".join(lines)
            )

        elif action == "add":
            if not word:
                return await interaction.response.send_message("give a word")
            w = word.lower()
            if w in cfg["slurs"]:
                return await interaction.response.send_message("already exists")

            cfg["slurs"].append(w)
            save_automod(AUTOMOD_DATA)
            await interaction.response.send_message(f"added `{censor_word(w)}`")

        elif action == "remove":
            if not word:
                return await interaction.response.send_message("give a word")
            w = word.lower()
            if w not in cfg["slurs"]:
                return await interaction.response.send_message("not found")

            cfg["slurs"].remove(w)
            save_automod(AUTOMOD_DATA)
            await interaction.response.send_message(f"removed `{censor_word(w)}`")

        else:
            await interaction.response.send_message(
                "actions: list, add, remove"
            )

async def setup(bot):
    await bot.add_cog(AutoModCog(bot))
