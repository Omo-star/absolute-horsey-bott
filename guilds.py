import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user
from economy_shared import state, save_state


def guild_root():
    return state.setdefault("guild_system_v1", {"next_id": 1, "guilds": {}, "user_to_guild": {}})


def user_guild_id(uid: int):
    return guild_root()["user_to_guild"].get(str(uid))


def get_guild(guild_id: int):
    return guild_root()["guilds"].get(str(guild_id))


def member_count(guild_data: dict) -> int:
    return len(guild_data.get("members", [])) if isinstance(guild_data.get("members", []), list) else 0


def guild_power(guild_data: dict) -> int:
    total = 0
    for uid in guild_data.get("members", []):
        data = get_user(int(uid))
        team = data.get("team", []) if isinstance(data.get("team", []), list) else []
        total += sum(int(animal.get("strength", 0) or 0) for animal in team if isinstance(animal, dict))
    return total


class GuildCommands(commands.Cog):
    guild_group = app_commands.Group(name="guild", description="Guild and faction commands")

    def __init__(self, bot):
        self.bot = bot

    @guild_group.command(name="create", description="Create a guild.")
    async def create(self, interaction: discord.Interaction, name: app_commands.Range[str, 3, 32]):
        root = guild_root()
        uid = str(interaction.user.id)
        if user_guild_id(interaction.user.id):
            await interaction.response.send_message("youre already in a guild", ephemeral=True)
            return

        gid = root["next_id"]
        root["next_id"] += 1
        root["guilds"][str(gid)] = {
            "id": gid,
            "name": str(name),
            "owner_id": interaction.user.id,
            "members": [uid],
            "bank": 0,
            "level": 1,
            "xp": 0,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        root["user_to_guild"][uid] = gid
        save_state()
        await interaction.response.send_message(f"guild created: **{name}** with id `{gid}`")

    @guild_group.command(name="join", description="Join a guild by id.")
    async def join(self, interaction: discord.Interaction, guild_id: int):
        root = guild_root()
        uid = str(interaction.user.id)
        if user_guild_id(interaction.user.id):
            await interaction.response.send_message("leave your current guild first", ephemeral=True)
            return
        guild_data = get_guild(guild_id)
        if not guild_data:
            await interaction.response.send_message("that guild doesnt exist", ephemeral=True)
            return
        if uid not in guild_data["members"]:
            guild_data["members"].append(uid)
        root["user_to_guild"][uid] = guild_id
        save_state()
        await interaction.response.send_message(f"you joined **{guild_data['name']}**")

    @guild_group.command(name="leave", description="Leave your current guild.")
    async def leave(self, interaction: discord.Interaction):
        root = guild_root()
        uid = str(interaction.user.id)
        gid = user_guild_id(interaction.user.id)
        if not gid:
            await interaction.response.send_message("youre not in a guild", ephemeral=True)
            return
        guild_data = get_guild(gid)
        if not guild_data:
            root["user_to_guild"].pop(uid, None)
            save_state()
            await interaction.response.send_message("your guild link was cleaned up")
            return
        if interaction.user.id == guild_data.get("owner_id") and member_count(guild_data) > 1:
            await interaction.response.send_message("transfer ownership or disband after everyone leaves", ephemeral=True)
            return
        guild_data["members"] = [m for m in guild_data.get("members", []) if m != uid]
        root["user_to_guild"].pop(uid, None)
        if not guild_data["members"]:
            root["guilds"].pop(str(gid), None)
        save_state()
        await interaction.response.send_message("you left the guild")

    @guild_group.command(name="info", description="View guild info.")
    async def info(self, interaction: discord.Interaction, guild_id: int = None):
        gid = guild_id or user_guild_id(interaction.user.id)
        if not gid:
            await interaction.response.send_message("youre not in a guild and didnt provide a guild id", ephemeral=True)
            return
        guild_data = get_guild(gid)
        if not guild_data:
            await interaction.response.send_message("that guild doesnt exist", ephemeral=True)
            return

        owner = interaction.guild.get_member(guild_data["owner_id"]) if interaction.guild else None
        owner_name = owner.display_name if owner else str(guild_data["owner_id"])
        members_display = []
        for raw_uid in guild_data.get("members", [])[:15]:
            member = interaction.guild.get_member(int(raw_uid)) if interaction.guild else None
            members_display.append(member.display_name if member else raw_uid)

        embed = discord.Embed(
            title=f"🏰 {guild_data['name']}",
            description=f"guild id `{guild_data['id']}`",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Core",
            value=(
                f"owner: `{owner_name}`\n"
                f"members: `{member_count(guild_data)}`\n"
                f"level: `{guild_data.get('level', 1)}`\n"
                f"xp: `{guild_data.get('xp', 0)}`\n"
                f"bank: `{guild_data.get('bank', 0):,}` horsenncy"
            ),
            inline=False
        )
        embed.add_field(name="Roster", value="\n".join(f"• {x}" for x in members_display) or "none", inline=False)
        embed.add_field(name="Guild Power", value=f"`{guild_power(guild_data):,}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @guild_group.command(name="deposit", description="Deposit horsenncy into your guild bank.")
    async def deposit(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1]):
        gid = user_guild_id(interaction.user.id)
        if not gid:
            await interaction.response.send_message("youre not in a guild", ephemeral=True)
            return
        guild_data = get_guild(gid)
        data = get_user(interaction.user.id)
        balance = int(data.get("balance", 0) or 0)
        if amount > balance:
            await interaction.response.send_message("not enough horsenncy", ephemeral=True)
            return
        data["balance"] = balance - int(amount)
        guild_data["bank"] = int(guild_data.get("bank", 0) or 0) + int(amount)
        guild_data["xp"] = int(guild_data.get("xp", 0) or 0) + max(1, int(amount) // 100)
        save_state()
        await interaction.response.send_message(f"deposited `{amount}` horsenncy into **{guild_data['name']}**")

    @guild_group.command(name="upgrade", description="Upgrade your guild using guild bank funds.")
    async def upgrade(self, interaction: discord.Interaction):
        gid = user_guild_id(interaction.user.id)
        if not gid:
            await interaction.response.send_message("youre not in a guild", ephemeral=True)
            return
        guild_data = get_guild(gid)
        if interaction.user.id != guild_data.get("owner_id"):
            await interaction.response.send_message("only the guild owner can upgrade it", ephemeral=True)
            return
        level = int(guild_data.get("level", 1) or 1)
        cost = level * 5000
        bank = int(guild_data.get("bank", 0) or 0)
        if bank < cost:
            await interaction.response.send_message(f"you need `{cost}` guild bank horsenncy for the next upgrade", ephemeral=True)
            return
        guild_data["bank"] = bank - cost
        guild_data["level"] = level + 1
        save_state()
        await interaction.response.send_message(f"**{guild_data['name']}** upgraded to level `{guild_data['level']}`")


async def setup(bot):
    print("Loading Guilds Cog...")
    await bot.add_cog(GuildCommands(bot))
    print("Guilds Cog Loaded!")
