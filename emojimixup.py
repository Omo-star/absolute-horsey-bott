import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, button, Button
import aiohttp
import asyncio
import json
import random
import io
import time
from pathlib import Path
from typing import Optional, Tuple, List

DISCOVERY_DATES = [
    "20201001",
    "20210218",
    "20210521",
    "20210831",
    "20220203",
    "20220823"
]

MAX_HISTORY = 25
MAX_FAVORITES = 50

class EmojiMixupView(View):
    def __init__(self, cog, user_id: int, e1: str, e2: str):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id
        self.e1 = e1
        self.e2 = e2

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your mix ✋", ephemeral=True)
            return False
        return True
    
    async def remix_core(self, interaction: discord.Interaction, a: str, b: str):
        try:
            file, url = await self.cog.get_mix_file(a, b)
        except Exception:
            raise
    
        self.e1, self.e2 = a, b
        embed = self.cog.build_embed(a, b)
        await self.cog.record(interaction, a, b, url)
    
        await interaction.response.edit_message(
            embed=embed,
            attachments=[file],
            view=self
        )

    @button(label="🔀 Remix", style=discord.ButtonStyle.primary)
    async def remix(self, interaction: discord.Interaction, _: Button):
        for _ in range(20):
            a, b = random.sample(self.cog.emojis, 2)
            try:
                await self.remix_core(interaction, a, b)
                return
            except Exception:
                continue
    
        await interaction.response.send_message(
            "❌ No valid mix found.",
            ephemeral=True
        )
    @button(label="↔️ Swap", style=discord.ButtonStyle.secondary)
    async def swap(self, interaction: discord.Interaction, _: Button):
        try:
            await self.remix_core(interaction, self.e2, self.e1)
        except Exception:
            await interaction.response.send_message(
                "❌ No valid mix found.",
                ephemeral=True
            )

    
    @button(label="🎲 Random Left", style=discord.ButtonStyle.success)
    async def rand_left(self, interaction: discord.Interaction, _: Button):
        for _ in range(20):
            a = random.choice(self.cog.emojis)
            try:
                await self.remix_core(interaction, a, self.e2)
                return
            except Exception:
                continue
    
        await interaction.response.send_message(
            "❌ No valid mix found.",
            ephemeral=True
        )
    @button(label="🎲 Random Right", style=discord.ButtonStyle.success)
    async def rand_right(self, interaction: discord.Interaction, _: Button):
        for _ in range(20):
            b = random.choice(self.cog.emojis)
            try:
                await self.remix_core(interaction, self.e1, b)
                return
            except Exception:
                continue
    
        await interaction.response.send_message(
            "❌ No valid mix found.",
            ephemeral=True
        )
    @button(label="⭐ Favorite", style=discord.ButtonStyle.success)
    async def favorite(self, interaction: discord.Interaction, _: Button):
        await interaction.response.defer(ephemeral=True)
        ok = await self.cog.add_favorite(interaction.user.id, self.e1, self.e2)
        await interaction.followup.send("⭐ Saved" if ok else "Already saved", ephemeral=True)

class EmojiMixupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.base = Path(__file__).parent
        self.session: Optional[aiohttp.ClientSession] = None
        self.emojis: List[str] = []
        self.mixups = {}
        self.data_path = self.base / "emojimixup_data.json"
        self.mixup_path = self.base / "mixup_emojis.json"
        self.data = {"history": {}, "favorites": {}}
        self.lock = asyncio.Lock()

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        self.emojis = (self.base / "emojis.txt").read_text(encoding="utf-8").splitlines()
        if self.mixup_path.exists():
            self.mixups = json.loads(self.mixup_path.read_text(encoding="utf-8"))
        if self.data_path.exists():
            self.data = json.loads(self.data_path.read_text(encoding="utf-8"))

    async def cog_unload(self):
        await self.session.close()

    def codepoints(self, e: str):
        return "_".join(hex(ord(c))[2:] for c in e)

    def key(self, a: str, b: str):
        return "_".join(sorted([a, b]))

    async def discover_mix(self, a: str, b: str) -> Optional[str]:
        cp1 = self.codepoints(a)
        cp2 = self.codepoints(b)
    
        attempts = [
            (cp1, cp2),
            (cp2, cp1)
        ]
    
        for d in DISCOVERY_DATES:
            for x, y in attempts:
                url = f"https://www.gstatic.com/android/keyboard/emojikitchen/{d}/u{x}/u{x}_u{y}.png"
                async with self.session.get(url) as r:
                    if r.status == 200:
                        async with self.lock:
                            self.mixups[self.key(a, b)] = f"{d}/u{x}/u{x}_u{y}.png"
                            self.mixup_path.write_text(
                                json.dumps(self.mixups, ensure_ascii=False, indent=2),
                                encoding="utf-8"
                            )
                        return url
        return None

    async def get_mix_file(self, a: str, b: str) -> Tuple[discord.File, str]:
        k = self.key(a, b)
        if k in self.mixups:
            path = self.mixups[k]
            url = f"https://www.gstatic.com/android/keyboard/emojikitchen/{path}"
        else:
            url = await self.discover_mix(a, b)
            if not url:
                raise ValueError
        async with self.session.get(url) as r:
            data = await r.read()
        return discord.File(io.BytesIO(data), filename="emoji.png"), url

    def build_embed(self, a: str, b: str):
        e = discord.Embed(title=f"{a} + {b}", color=0xF7C873)
        e.set_image(url="attachment://emoji.png")
        e.set_footer(text="Emoji Kitchen · Auto-discovered")
        return e

    async def record(self, interaction: discord.Interaction, a: str, b: str, url: str):
        uid = str(interaction.user.id)
        self.data.setdefault("history", {}).setdefault(uid, [])
        self.data["history"][uid].insert(0, {"a": a, "b": b, "url": url, "ts": time.time()})
        self.data["history"][uid] = self.data["history"][uid][:MAX_HISTORY]
        self.data_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def add_favorite(self, uid: int, a: str, b: str):
        u = str(uid)
        k = self.key(a, b)
        self.data.setdefault("favorites", {}).setdefault(u, [])
        if k in self.data["favorites"][u]:
            return False
        self.data["favorites"][u].insert(0, k)
        self.data["favorites"][u] = self.data["favorites"][u][:MAX_FAVORITES]
        self.data_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    async def emoji_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=e, value=e)
            for e in self.emojis
            if current in e
        ][:25]

    @app_commands.command(name="emojimixup", description="Mix emojis (auto-discovery enabled)")
    @app_commands.autocomplete(emoji1=emoji_autocomplete, emoji2=emoji_autocomplete)
    async def emojimixup(self, interaction: discord.Interaction, emoji1: str, emoji2: str):
        await interaction.response.defer()
        if emoji1 not in self.emojis or emoji2 not in self.emojis:
            await interaction.followup.send("❌ Unsupported emoji.", ephemeral=True)
            return
        try:
            file, url = await self.get_mix_file(emoji1, emoji2)
        except Exception:
            await interaction.followup.send("❌ No mix found.", ephemeral=True)
            return
        view = EmojiMixupView(self, interaction.user.id, emoji1, emoji2)
        embed = self.build_embed(emoji1, emoji2)
        await self.record(interaction, emoji1, emoji2, url)
        await interaction.followup.send(embed=embed, file=file, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(EmojiMixupCog(bot))
