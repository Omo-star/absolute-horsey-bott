import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from io import BytesIO
import aiohttp
import asyncio
import json
from pathlib import Path

DATA_PATH = Path("badges_data.json")

BADGE_TEMPLATES = {
    "discord": (40, 40, 40),
    "agent": (20, 60, 90),
    "security": (80, 20, 20),
}

class BadgeView(View):
    def __init__(self, cog, user):
        super().__init__(timeout=60)
        self.cog = cog
        self.user = user
        options = [
            discord.SelectOption(label=name.title(), value=name)
            for name in BADGE_TEMPLATES
        ]
        self.add_item(BadgeSelect(self, options))

class BadgeSelect(Select):
    def __init__(self, view, options):
        super().__init__(placeholder="Select a badge", options=options)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.user.id:
            await interaction.response.send_message("Not for you", ephemeral=True)
            return
        await interaction.response.defer()
        badge = self.values[0]
        image = await self.view_ref.cog.create_badge(interaction.user, badge)
        file = discord.File(image, filename="badge.gif" if image.name.endswith("gif") else "badge.png")
        await interaction.followup.send(file=file)

class BadgeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        if not DATA_PATH.exists():
            DATA_PATH.write_text(json.dumps({}))

    async def cog_unload(self):
        await self.session.close()

    def load_data(self):
        return json.loads(DATA_PATH.read_text())

    def save_data(self, data):
        DATA_PATH.write_text(json.dumps(data))

    async def fetch_avatar(self, user: discord.User, animated=False):
        fmt = "gif" if animated and user.display_avatar.is_animated() else "png"
        avatar = user.display_avatar.with_format(fmt)
        buf = BytesIO()
        await avatar.save(buf)
        buf.seek(0)
        return Image.open(buf)

    def draw_base(self, user, badge):
        base = Image.new("RGBA", (600, 300), BADGE_TEMPLATES[badge] + (255,))
        draw = ImageDraw.Draw(base)
        font = ImageFont.load_default()
        draw.text((200, 60), user.display_name, fill=(255, 255, 255), font=font)
        draw.text((200, 100), f"ID {user.id}", fill=(200, 200, 200), font=font)
        draw.text((200, 140), badge.upper(), fill=(255, 120, 120), font=font)
        return base

    def make_static_badge(self, base, avatar):
        avatar = avatar.resize((128, 128))
        base.paste(avatar, (40, 80))
        buf = BytesIO()
        base.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "badge.png"
        return buf

    def make_gif_badge(self, base, avatar):
        frames = []
        for frame in ImageSequence.Iterator(avatar):
            temp = base.copy()
            frame = frame.convert("RGBA").resize((128, 128))
            temp.paste(frame, (40, 80))
            frames.append(temp)
        buf = BytesIO()
        frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=avatar.info.get("duration", 60),
            loop=0,
        )
        buf.seek(0)
        buf.name = "badge.gif"
        return buf

    async def create_badge(self, user, badge):
        base = self.draw_base(user, badge)
        animated = user.display_avatar.is_animated()
        avatar = await self.fetch_avatar(user, animated)
        loop = asyncio.get_running_loop()
        if animated:
            return await loop.run_in_executor(None, self.make_gif_badge, base, avatar)
        return await loop.run_in_executor(None, self.make_static_badge, base, avatar)

    @app_commands.command(name="badge", description="Create and select profile badges")
    async def badge(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Choose your badge",
            view=BadgeView(self, interaction.user),
            ephemeral=True,
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(BadgeCog(bot))
