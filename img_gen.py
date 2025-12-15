import asyncio
import base64
import io
import os
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
import google.generativeai as genai


OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_KEY)

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

async def _gen_openai(prompt: str):
    try:
        loop = asyncio.get_event_loop()

        def call():
            return openai_client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024"
            )

        resp = await asyncio.wait_for(loop.run_in_executor(None, call), timeout=20)
        img_b64 = resp.data[0].b64_json
        return base64.b64decode(img_b64)

    except Exception:
        return None


async def _gen_openrouter(prompt: str):
    if not OPENROUTER_KEY:
        return None

    url = "https://openrouter.ai/api/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "fusbot",
    }
    payload = {
        "model": "stabilityai/stable-diffusion-xl",
        "prompt": prompt,
        "size": "1024x1024",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=25) as r:
                data = await r.json()
                img_b64 = data["data"][0]["b64_json"]
                return base64.b64decode(img_b64)

    except Exception:
        return None


async def _gen_gemini(prompt: str):
    if not GEMINI_KEY:
        return None

    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash-image")
        resp = model.generate_content(prompt)

        for part in resp.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                return part.inline_data.data

        return None

    except Exception:
        return None

async def generate_image(prompt: str):
    for fn in (_gen_openai, _gen_openrouter, _gen_gemini):
        img = await fn(prompt)
        if img:
            return img
    return None


class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="img",
        description="Generate an AI image (OpenAI → OpenRouter → Gemini)"
    )
    @app_commands.describe(prompt="Describe the image you want")
    async def img(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(thinking=True)

        img_bytes = await generate_image(prompt)

        if not img_bytes:
            return await interaction.followup.send(
                "❌ Image generation failed on all providers."
            )

        file = discord.File(io.BytesIO(img_bytes), filename="image.png")
        await interaction.followup.send(file=file)

async def setup(bot):
    await bot.add_cog(ImageGen(bot))
