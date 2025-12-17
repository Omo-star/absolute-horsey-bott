import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, button, Modal, TextInput, Select
import asyncio
import logging
import math
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import aiohttp
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    ColorClip,
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip

def text_clip(txt, font_path, fontsize, color, duration, pos):
    font = ImageFont.truetype(font_path, fontsize)

    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    w, h = d.textbbox((0, 0), txt, font=font)[2:]

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), txt, font=font, fill=color)

    return (
        ImageClip(np.array(img))
        .set_duration(duration)
        .set_position(pos)
    )


log = logging.getLogger("rave")

DATA = Path("data/rave")
ASSETS = DATA / "assets"
UPLOADS = DATA / "uploads"

DATA.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(exist_ok=True)
UPLOADS.mkdir(exist_ok=True)

FONT_URL = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/Verdana.ttf"
FONT = ASSETS / "Verdana.ttf"

CRAB_TEMPLATE = ASSETS / "crab_template.mp4"

QUEUE = asyncio.Semaphore(2)

class Mode(str, Enum):
    TEMPLATE = "Crab Rave"
    BUILD = "Build"

class Base(str, Enum):
    PULSE = "Pulse"
    CHECKER = "Checker"
    STROBE = "Strobe"
    GRADIENT = "Gradient"
    UPLOAD = "Upload"

class Anim(str, Enum):
    STATIC = "Static"
    BOUNCE = "Bounce"

class Ease(str, Enum):
    LINEAR = "Linear"
    INOUT = "EaseInOut"
    ELASTIC = "Elastic"

@dataclass
class Cfg:
    mode: Mode = Mode.TEMPLATE
    base: Base = Base.PULSE
    anim: Anim = Anim.BOUNCE
    ease: Ease = Ease.INOUT

    top: str = "TOP TEXT"
    bottom: str = "BOTTOM TEXT"

    font: int = 56
    top_y: int = 200
    bottom_y: int = 270

    dur: float = 15.4
    fps: int = 24
    bpm: int = 128

    upload: str = ""

def now():
    return str(int(time.time() * 1000))

class UploadKeyModal(Modal, title="Set Upload Key"):
    key = TextInput(label="Upload key", required=True)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.key.default = cfg.upload

    async def on_submit(self, i):
        self.cfg.upload = self.key.value.strip()
        await i.response.send_message("Upload key set.", ephemeral=True)

class TextModal(Modal, title="Text"):
    t = TextInput(label="Top", max_length=64)
    b = TextInput(label="Bottom", max_length=64)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.t.default = cfg.top
        self.b.default = cfg.bottom

    async def on_submit(self, i):
        self.cfg.top = self.t.value
        self.cfg.bottom = self.b.value
        await i.response.send_message("Updated.", ephemeral=True)

class ModeSelect(Select):
    def __init__(self, view):
        self.view_ref = view
        super().__init__(
            placeholder="Mode",
            options=[discord.SelectOption(label=m.value) for m in Mode],
        )

    async def callback(self, interaction):
        self.view_ref.cfg.mode = Mode(self.values[0])
        await interaction.response.defer()
        await self.view_ref.refresh(interaction)
class BaseSelect(Select):
    def __init__(self, view):
        self.view_ref = view
        super().__init__(
            placeholder="Build Base",
            options=[discord.SelectOption(label=b.value) for b in Base],
        )

    def sync_state(self):
        self.disabled = self.view_ref.cfg.mode == Mode.TEMPLATE

    async def callback(self, interaction):
        self.view_ref.cfg.base = Base(self.values[0])
        await interaction.response.defer()
        await self.view_ref.refresh(interaction)


class AnimSelect(Select):
    def __init__(self, view):
        self.view_ref = view
        super().__init__(
            placeholder="Animation",
            options=[discord.SelectOption(label=a.value) for a in Anim],
        )

    async def callback(self, interaction):
        self.view_ref.cfg.anim = Anim(self.values[0])
        await interaction.response.defer()
        await self.view_ref.refresh(interaction)

class RaveView(View):
    def __init__(self, cog, uid):
        super().__init__(timeout=900)
        self.cog = cog
        self.uid = uid
        self.cfg = Cfg()
        self.status = "Idle"

        self.add_item(ModeSelect(self))
        self.add_item(BaseSelect(self))
        self.add_item(AnimSelect(self))
        for item in self.children:
            if isinstance(item, BaseSelect):
                item.sync_state()
    async def interaction_check(self, i):
        return i.user.id == self.uid

    def embed(self):
        e = discord.Embed(title="🎛️ Rave Builder", color=0x2B2D31)
        c = self.cfg
        e.add_field(name="Mode", value=c.mode.value)
        e.add_field(name="Base", value=c.base.value)
        e.add_field(name="Anim", value=c.anim.value)
        e.add_field(name="Text", value=f"{c.top}\n{c.bottom}", inline=False)
        if c.upload:
            e.add_field(name="Upload", value=c.upload)
        e.set_footer(text=self.status)
        return e

    async def refresh(self, i):
        for item in self.children:
            if isinstance(item, BaseSelect):
                item.sync_state()
    
        await i.message.edit(embed=self.embed(), view=self)


    @button(label="Text", style=discord.ButtonStyle.primary)
    async def btn_text(self, i, _):
        await i.response.send_modal(TextModal(self.cfg))

    @button(label="Set Upload", style=discord.ButtonStyle.secondary)
    async def btn_upload(self, i, _):
        await i.response.send_modal(UploadKeyModal(self.cfg))

    @button(label="Preview", style=discord.ButtonStyle.success)
    async def btn_preview(self, i, _):
        if self.cfg.base == Base.UPLOAD and not self.cfg.upload:
            await i.response.send_message(
                "⚠️ Please set an upload key first.",
                ephemeral=True,
            )
            return
        await self.run(i, True)
    
    
    @button(label="Render", style=discord.ButtonStyle.success)
    async def btn_render(self, i, _):
        if self.cfg.base == Base.UPLOAD and not self.cfg.upload:
            await i.response.send_message(
                "⚠️ Please set an upload key first.",
                ephemeral=True,
            )
            return
        await self.run(i, False)

    async def run(self, i, preview):
        async with QUEUE:
            self.status = "Rendering"
            await i.response.edit_message(embed=self.embed(), view=self)
    
            try:
                out = await asyncio.to_thread(
                    self.cog.render, self.uid, self.cfg, preview
                )
            except Exception as e:
                self.status = "Error"
                await i.followup.send(
                    f"❌ **Render failed:** {e}",
                    ephemeral=True,
                )
                await i.message.edit(embed=self.embed(), view=self)
                return
    
            await i.followup.send(file=discord.File(out))
            os.remove(out)
            self.stop()


class RaveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure(self):

        if not FONT.exists():
            async with aiohttp.ClientSession() as s:
                async with s.get(FONT_URL) as r:
                    FONT.write_bytes(await r.read())

        if not CRAB_TEMPLATE.exists():
            raise RuntimeError(
                "Missing crab_template.mp4 in data/rave/assets/"
            )

    def render(self, uid, cfg, preview):
        dur = 6 if preview else cfg.dur
        size = (854, 480) if preview else (1280, 720)

        if cfg.mode == Mode.TEMPLATE:
            clip = (
                VideoFileClip(str(CRAB_TEMPLATE))
                .subclip(0, dur)
                .fx(mp_video.fx.resize, size)
            )

        elif cfg.base == Base.UPLOAD:
            if not cfg.upload:
                raise ValueError("No upload key set")
        
            path = UPLOADS / f"{uid}_{cfg.upload}"
            if not path.exists():
                raise FileNotFoundError(f"Upload not found: {path}")
        
            clip = (
                VideoFileClip(str(path))
                .loop(duration=dur)
                .resize(height=size[1])
            )
        else:
            clip = ColorClip(size, color=(10, 10, 10), duration=dur)

        def pos(y):
            def f(t):
                p = math.sin(2 * math.pi * cfg.bpm / 60 * t)
                dy = 30 * p if cfg.anim == Anim.BOUNCE else 0
                return ("center", y + dy)
            return f
        
        top = text_clip(cfg.top.upper(), str(FONT), cfg.font, "white", dur, pos(cfg.top_y))
        bottom = text_clip(cfg.bottom.upper(), str(FONT), cfg.font, "white", dur, pos(cfg.bottom_y))


        comp = CompositeVideoClip([clip, top, bottom], size=size)
        out = DATA / f"{uid}_{now()}.mp4"
        comp.write_videofile(str(out), fps=cfg.fps, preset="superfast", logger=None)

        comp.close()
        clip.close()
        return out

    @app_commands.command(
        name="rave",
        description="Open the interactive rave video builder"
    )
    async def rave(self, i):
        await self.ensure()
        v = RaveView(self, i.user.id)
        await i.response.send_message(embed=v.embed(), view=v)

    @app_commands.command(
        name="ravebg",
        description="Upload a background video for rave builds"
    )
    async def ravebg(self, i, file: discord.Attachment):
        key = now() + "_" + file.filename
        await file.save(UPLOADS / f"{i.user.id}_{key}")
        await i.response.send_message(
            f"Saved. Upload key: `{key}`",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(RaveCog(bot))

