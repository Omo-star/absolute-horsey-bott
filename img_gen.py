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
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("imagegen")


OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_KEY)

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

async def _gen_openai(prompt: str):
    log.info("OpenAI: generating image")

    try:
        resp = openai_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            response_format="b64_json",
        )

        img = base64.b64decode(resp.data[0].b64_json)
        log.info("OpenAI: success (%d bytes)", len(img))
        return img

    except Exception as e:
        log.error("OpenAI failed: %s", e, exc_info=True)
        return None

async def _gen_openrouter(prompt: str):
    if not OPENROUTER_KEY:
        log.warning("OpenRouter: no API key")
        return None

    log.info("OpenRouter: generating image")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://example.com",
                    "X-Title": "fusbot",
                },
                json={
                    "model": "stabilityai/sdxl",
                    "prompt": prompt,
                    "size": "1024x1024",
                    "response_format": "b64_json",
                },
                timeout=30,
            ) as r:

                if r.status != 200:
                    text = await r.text()
                    log.warning(
                        "OpenRouter HTTP %s: %s",
                        r.status,
                        text[:300],
                    )
                    return None

                data = await r.json()
                img = base64.b64decode(data["data"][0]["b64_json"])

                log.info("OpenRouter: success (%d bytes)", len(img))
                return img

    except Exception as e:
        log.error("OpenRouter failed: %s", e, exc_info=True)
        return None

async def _gen_gemini(prompt: str):
    if not GEMINI_KEY:
        log.warning("Gemini: no API key")
        return None

    log.info("Gemini: generating image")

    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro-vision-latest")

        resp = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "image/png"},
        )

        for part in resp.candidates[0].content.parts:
            if part.inline_data:
                img = part.inline_data.data
                log.info("Gemini: success (%d bytes)", len(img))
                return img

        log.warning("Gemini: no image in response")
        return None

    except Exception as e:
        log.error("Gemini failed: %s", e, exc_info=True)
        return None

async def generate_image(prompt: str):
    for fn in (_gen_openai, _gen_openrouter, _gen_gemini):
        log.info("Trying provider: %s", fn.__name__)
        img = await fn(prompt)
        if img:
            log.info("Provider %s succeeded", fn.__name__)
            return img
        log.info("Provider %s failed, trying next", fn.__name__)

    log.error("All image providers failed")
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
