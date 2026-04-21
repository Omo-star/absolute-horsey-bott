import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy_shared import state, save_state


def setup_root():
    return state.setdefault("server_setup_v2", {})


def guild_setup_data(guild_id: int):
    root = setup_root()
    key = str(guild_id)
    if key not in root:
        root[key] = {
            "onboarding_channel_id": None,
            "tips_enabled": True,
            "last_posted_at": None,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        save_state()
    return root[key]


def channel_text(guild: discord.Guild, channel_id):
    if not channel_id:
        return "not set"
    channel = guild.get_channel(int(channel_id))
    return channel.mention if channel else f"`{channel_id}`"


def onboarding_embed(guild: discord.Guild, config: dict):
    embed = discord.Embed(
        title=f"👋 welcome to {guild.name}'s FuSBot guide",
        description="this bot does a lot, so here’s the clean starting point before you mash `/` and get lost",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(
        name="Start Here",
        value=(
            "`/help start` for the beginner guide\n"
            "`/profile` to see your account\n"
            "`/balance` to check money\n"
            "`/daily` and `/work` to start earning"
        ),
        inline=False
    )
    embed.add_field(
        name="Best Starter Routes",
        value=(
            "**money**\n"
            "`/daily` → `/work` → `/shop` or `/stocks`\n\n"
            "**creatures**\n"
            "`/hunt` or `/fish` → `/team list` → `/battle`\n\n"
            "**deep modes**\n"
            "`/dungeon` or `/voidmaze` or `/arena`\n\n"
            "**ai**\n"
            "`/roast` or `/code_list` → `/hack`"
        ),
        inline=False
    )
    embed.add_field(
        name="Need More Help?",
        value=(
            "`/help economy`\n"
            "`/help adventure`\n"
            "`/help deep`\n"
            "`/help ai`\n"
            "`/help fun`"
        ),
        inline=False
    )
    if config.get("tips_enabled", True):
        embed.add_field(
            name="Starter Tip",
            value="new people should try `/profile`, `/daily`, `/work`, and `/help adventure` first",
            inline=False
        )
    embed.set_footer(text="server onboarding panel")
    return embed


def setup_view_embed(guild: discord.Guild, config: dict):
    embed = discord.Embed(
        title="🛠️ server setup",
        description=f"current FuSBot onboarding setup for **{guild.name}**",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(
        name="Current Settings",
        value=(
            f"onboarding channel: {channel_text(guild, config.get('onboarding_channel_id'))}\n"
            f"tips enabled: `{'yes' if config.get('tips_enabled', True) else 'no'}`\n"
            f"last onboarding post: `{config.get('last_posted_at') or 'never'}`"
        ),
        inline=False
    )
    embed.add_field(
        name="Recommended Flow",
        value=(
            "1. run `/setup channel`\n"
            "2. run `/setup post`\n"
            "3. test `/help start`\n"
            "4. optionally configure automod"
        ),
        inline=False
    )
    embed.add_field(
        name="Useful Admin Commands",
        value=(
            "`/setup view`\n"
            "`/setup channel`\n"
            "`/setup tips`\n"
            "`/setup post`\n"
            "`/setup reset`\n"
            "`/help admin`"
        ),
        inline=False
    )
    return embed


class SetupCommands(commands.Cog):
    setup_group = app_commands.Group(name="setup", description="Server onboarding and setup commands")

    def __init__(self, bot):
        self.bot = bot

    async def admin_check(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("this only works in a server", ephemeral=True)
            return False
        perms = interaction.user.guild_permissions
        if not perms.manage_guild and not perms.administrator:
            await interaction.response.send_message("you need manage server or administrator for this", ephemeral=True)
            return False
        return True

    @setup_group.command(name="view", description="View the current onboarding setup for this server.")
    async def view(self, interaction: discord.Interaction):
        if not await self.admin_check(interaction):
            return
        config = guild_setup_data(interaction.guild.id)
        await interaction.response.send_message(embed=setup_view_embed(interaction.guild, config), ephemeral=True)

    @setup_group.command(name="channel", description="Set the channel used for onboarding posts.")
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self.admin_check(interaction):
            return
        config = guild_setup_data(interaction.guild.id)
        config["onboarding_channel_id"] = channel.id
        save_state()
        await interaction.response.send_message(f"onboarding channel set to {channel.mention}", ephemeral=True)

    @setup_group.command(name="tips", description="Turn onboarding tips on or off.")
    async def tips(self, interaction: discord.Interaction, enabled: bool):
        if not await self.admin_check(interaction):
            return
        config = guild_setup_data(interaction.guild.id)
        config["tips_enabled"] = bool(enabled)
        save_state()
        await interaction.response.send_message(f"onboarding tips are now `{'on' if enabled else 'off'}`", ephemeral=True)

    @setup_group.command(name="post", description="Post the onboarding guide in the setup channel or current channel.")
    async def post(self, interaction: discord.Interaction):
        if not await self.admin_check(interaction):
            return

        config = guild_setup_data(interaction.guild.id)
        target_channel = None

        channel_id = config.get("onboarding_channel_id")
        if channel_id:
            target_channel = interaction.guild.get_channel(int(channel_id))

        if target_channel is None:
            if isinstance(interaction.channel, discord.TextChannel):
                target_channel = interaction.channel
            else:
                await interaction.response.send_message("i couldnt find a valid text channel to post in", ephemeral=True)
                return

        embed = onboarding_embed(interaction.guild, config)
        await target_channel.send(embed=embed)
        config["last_posted_at"] = datetime.datetime.utcnow().isoformat()
        save_state()

        if target_channel.id == interaction.channel.id:
            await interaction.response.send_message("posted the onboarding guide here", ephemeral=True)
        else:
            await interaction.response.send_message(f"posted the onboarding guide in {target_channel.mention}", ephemeral=True)

    @setup_group.command(name="reset", description="Reset this server's setup data.")
    async def reset(self, interaction: discord.Interaction):
        if not await self.admin_check(interaction):
            return
        root = setup_root()
        root.pop(str(interaction.guild.id), None)
        save_state()
        await interaction.response.send_message("server setup data reset", ephemeral=True)


async def setup(bot):
    print("Loading Server Setup Cog...")
    await bot.add_cog(SetupCommands(bot))
    print("Server Setup Cog Loaded!")
