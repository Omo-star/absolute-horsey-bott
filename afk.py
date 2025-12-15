import discord
import datetime
from discord.ext import commands
from discord import app_commands
from economy_shared import state, save_state


MAX_PINGS = 25


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        state.setdefault("afk", {})

    @app_commands.command(name="afk", description="Set yourself as AFK.")
    async def afk(self, interaction: discord.Interaction, message: str | None = None):
        uid = str(interaction.user.id)

        state["afk"][uid] = {
            "message": message or "AFK",
            "since": int(datetime.datetime.utcnow().timestamp()),
            "pings": [],
        }
        save_state()

        embed = discord.Embed(
            title="💤 AFK Enabled",
            description=f"**Message:** {state['afk'][uid]['message']}",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="AFK clears automatically when you speak.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        afk = state.setdefault("afk", {})
        author_id = str(message.author.id)
        touched_state = False

        if author_id in afk:
            data = afk.pop(author_id)
            touched_state = True

            embed = discord.Embed(
                title="👋 Welcome back",
                description=f"You were AFK since <t:{data['since']}:R>.",
                color=discord.Color.green(),
            )

            await message.channel.send(
                embed=embed,
                view=PingView(message.author.id, data),
                reference=message.to_reference(fail_if_not_exists=False),
            )

        for member in message.mentions:
            uid = str(member.id)
            if uid not in afk:
                continue

            data = afk[uid]
            entry = f"{message.author.mention} in {message.channel.mention}"

            if len(data["pings"]) < MAX_PINGS:
                data["pings"].append(entry)
                touched_state = True

            embed = discord.Embed(
                description=(
                    f"{member.mention} is currently AFK\n"
                    f"**Reason:** {data['message']}\n"
                    f"**Since:** <t:{data['since']}:R>"
                ),
                color=discord.Color.orange(),
            )

            await message.channel.send(
                embed=embed,
                reference=message.to_reference(fail_if_not_exists=False),
                delete_after=15,
            )

        if touched_state:
            save_state()


class PingView(discord.ui.View):
    def __init__(self, owner_id: int, data: dict):
        super().__init__(timeout=60)
        self.owner_id = owner_id
        self.data = data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "This isn't your AFK summary.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Show Pings", style=discord.ButtonStyle.secondary)
    async def show_pings(self, interaction: discord.Interaction, _):
        if not self.data["pings"]:
            return await interaction.response.send_message(
                "No one pinged you while AFK 😌", ephemeral=True
            )

        embed = discord.Embed(
            title="🔔 Pings While AFK",
            description="\n".join(self.data["pings"]),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AFK(bot))
