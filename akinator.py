import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, button, Button
import akinator

ANSWER_MAP = {
    "yes": "y",
    "no": "n",
    "idk": "idk",
    "probably": "p",
    "probably_not": "pn",
}

class AkiView(View):
    def __init__(self, aki: Akinator, user_id: int):
        super().__init__(timeout=300)
        self.aki = aki
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This isn’t your Akinator game.", ephemeral=True
            )
            return False
        return True

    async def handle_answer(self, interaction: discord.Interaction, answer: str):
        await interaction.response.defer()

        try:
            question = await self.aki.answer(answer)
        except Exception:
            await interaction.followup.send(
                "❌ Akinator encountered an error. Game ended.", ephemeral=True
            )
            self.stop()
            return

        if self.aki.progression >= 80:
            await self.aki.win()
            guess = self.aki.first_guess

            embed = discord.Embed(
                title="🎯 I guess...",
                description=f"**{guess['name']}**\n{guess['description']}",
                color=0xE8BC90,
            )
            if guess.get("absolute_picture_path"):
                embed.set_image(url=guess["absolute_picture_path"])

            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=None,
            )
            self.stop()
        else:
            embed = discord.Embed(
                title="🧠 Akinator",
                description=question,
                color=0xE8BC90,
            )
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self,
            )

    @button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _: Button):
        await self.handle_answer(interaction, ANSWER_MAP["yes"])

    @button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, _: Button):
        await self.handle_answer(interaction, ANSWER_MAP["no"])

    @button(label="I don't know", style=discord.ButtonStyle.secondary)
    async def idk(self, interaction: discord.Interaction, _: Button):
        await self.handle_answer(interaction, ANSWER_MAP["idk"])

    @button(label="Probably", style=discord.ButtonStyle.primary)
    async def probably(self, interaction: discord.Interaction, _: Button):
        await self.handle_answer(interaction, ANSWER_MAP["probably"])

    @button(label="Probably not", style=discord.ButtonStyle.primary)
    async def probably_not(self, interaction: discord.Interaction, _: Button):
        await self.handle_answer(interaction, ANSWER_MAP["probably_not"])


class AkinatorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="aki", description="Play Akinator with buttons")
    async def aki(self, interaction: discord.Interaction):
        await interaction.response.defer()

        aki = akinator.Akinator()
        try:
            question = await aki.start_game(language="en")
        except Exception:
            await interaction.followup.send(
                "❌ Failed to connect to Akinator servers."
            )
            return

        embed = discord.Embed(
            title="🧠 Akinator",
            description=question,
            color=0xE8BC90,
        )

        view = AkiView(aki, interaction.user.id)

        await interaction.followup.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(AkinatorCog(bot))
