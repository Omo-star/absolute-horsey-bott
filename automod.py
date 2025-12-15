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
TEST_USER_IDS = {1238242784679563265}
AUTOMOD_BLOCKED_MESSAGES: set[int] = set()

WINDOW = 6
COUNT = 5

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
        self.msg_times = defaultdict(lambda: deque(maxlen=10))
        self.offences = defaultdict(lambda: defaultdict(int))

    def get_cfg(self, guild_id: int):
        if str(guild_id) not in AUTOMOD_DATA:
            AUTOMOD_DATA[str(guild_id)] = {
                "enabled": False,
                "slurs": []
            }
            save_automod(AUTOMOD_DATA)
        return AUTOMOD_DATA[str(guild_id)]

    def record_message(self, guild_id: int, user_id: int):
        now = time.time()
        self.msg_times[(guild_id, user_id)].append(now)
        
    def is_spam(self, guild_id: int, user_id: int) -> bool:
        now = time.time()
        times = self.msg_times[(guild_id, user_id)]
    
        recent = [t for t in times if now - t <= WINDOW]
    
        if len(recent) >= COUNT:
            return True
    
        return False

    def contains_slur(self, text: str, slurs: list[str]) -> str | None:
        lowered = text.lower()
        for s in slurs:
            if re.search(rf"\b{re.escape(s)}\b", lowered):
                return s
        return None
        
    async def handle_message(self, message: discord.Message) -> bool:
        if not message.guild or message.author.bot:
            return False
    
        if has_mod_perms(message.author):
            return False
    
        cfg = self.get_cfg(message.guild.id)
        if not cfg["enabled"]:
            return False
    
        self.record_message(message.guild.id, message.author.id)
        
        if self.is_spam(message.guild.id, message.author.id):
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
        guild = message.guild
        user = message.author

        gid = guild.id
        uid = user.id

        self.offences[gid][uid] += 1
        level = self.offences[gid][uid]

        try:
            await message.delete()
        except:
            pass

        if level == 1:
            await message.channel.send(
                f"{user.mention} warning: stop ({reason}). next offence = mute."
            )

        elif level == 2:
            try:
                await user.timeout(
                    datetime.timedelta(minutes=5),
                    reason=f"automod: {reason}"
                )
            except:
                pass
            await message.channel.send(
                f"{user.mention} muted for 5 minutes. reason: {reason}."
            )
        
        elif level == 3:
            try:
                await guild.kick(user, reason=f"automod: {reason}")
                await message.channel.send(
                    f"🚪 **{user} was kicked** due to **{reason}**."
                )
            except:
                pass
        
        elif level >= 4:
            try:
                await guild.ban(user, reason=f"automod: {reason}")
                await message.channel.send(
                    f"🔨 **{user} was banned** due to **{reason}**."
                )
            except:
                pass


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
            msg = f"🔄 automod points reset for **{user}**."
        else:
            msg = f"ℹ️ **{user}** had no automod points."

        await interaction.response.send_message(msg)

    
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
