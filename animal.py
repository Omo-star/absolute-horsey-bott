import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging

log = logging.getLogger("animals")

ANIMAL_ENDPOINTS = {
    "cat": "https://some-random-api.com/animal/cat",
    "dog": "https://some-random-api.com/animal/dog",
    "fox": "https://some-random-api.com/animal/fox",
    "panda": "https://some-random-api.com/animal/panda",
    "red_panda": "https://some-random-api.com/animal/red_panda",
    "koala": "https://some-random-api.com/animal/koala",
    "bird": "https://some-random-api.com/animal/bird",
    "raccoon": "https://some-random-api.com/animal/raccoon",
    "kangaroo": "https://some-random-api.com/animal/kangaroo",
}


class AnimalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def fetch_animal(self, interaction: discord.Interaction, animal: str):
        url = ANIMAL_ENDPOINTS[animal]

        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
        except Exception:
            log.exception("Animal API failed")
            await interaction.followup.send("❌ Failed to fetch animal.")
            return

        image = data.get("image")
        fact = data.get("fact")

        embed = discord.Embed(
            title=animal.replace("_", " ").title(),
            description=fact,
            color=0xF5A9B8,
        )

        if image:
            embed.set_image(url=image)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="animal", description="Get a random animal")
    @app_commands.choices(
        animal=[
            app_commands.Choice(name="Cat", value="cat"),
            app_commands.Choice(name="Dog", value="dog"),
            app_commands.Choice(name="Fox", value="fox"),
            app_commands.Choice(name="Panda", value="panda"),
            app_commands.Choice(name="Red Panda", value="red_panda"),
            app_commands.Choice(name="Koala", value="koala"),
            app_commands.Choice(name="Bird", value="bird"),
            app_commands.Choice(name="Raccoon", value="raccoon"),
            app_commands.Choice(name="Kangaroo", value="kangaroo"),
        ]
    )
    async def animal(
        self,
        interaction: discord.Interaction,
        animal: app_commands.Choice[str],
    ):
        await interaction.response.defer()
        await self.fetch_animal(interaction, animal.value)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnimalCog(bot))
