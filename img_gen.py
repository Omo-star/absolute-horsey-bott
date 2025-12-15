import os
import io
import base64
import logging
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("imagegen")

REPLICATE_KEY = os.getenv("REPLICATE_API_TOKEN")
STABILITY_KEY = os.getenv("STABILITY_API_KEY")
SDXL_VERSION = "7762fd07cf82c948538e2d7cbbd1b0b39d3c0c7a7a0b6e7c2d9bde6c8f3b3c4"

async def _gen_replicate(prompt: str):
    if not REPLICATE_KEY:
        return None

    log.info("Replicate: generating image")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.replicate.com/v1/models/stability-ai/sdxl/versions/{SDXL_VERSION}/predictions",
                headers={
                    "Authorization": f"Bearer {REPLICATE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "wait",
                },
                json={
                    "input": {
                        "prompt": prompt,
                        "width": 1024,
                        "height": 1024,
                        "num_outputs": 1,
                    }
                },
                timeout=90,
            ) as r:
                if r.status != 201:
                    log.warning("Replicate HTTP %s: %s", r.status, await r.text())
                    return None

                data = await r.json()
                output = data.get("output")

                if not output:
                    log.warning("Replicate returned no output")
                    return None

                image_url = output[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=30) as r:
                img = await r.read()
                log.info("Replicate: success (%d bytes)", len(img))
                return img

    except Exception as e:
        log.error("Replicate failed: %s", e, exc_info=True)
        return None


async def _gen_stability(prompt: str):
    if not STABILITY_KEY:
        return None

    log.info("Stability: generating image")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {STABILITY_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "text_prompts": [{"text": prompt}],
                    "width": 1024,
                    "height": 1024,
                    "samples": 1,
                },
                timeout=30,
            ) as r:
                if r.status != 200:
                    log.warning("Stability HTTP %s", r.status)
                    return None

                data = await r.json()
                img = base64.b64decode(data["artifacts"][0]["base64"])
                log.info("Stability: success (%d bytes)", len(img))
                return img

    except Exception as e:
        log.error("Stability failed: %s", e, exc_info=True)
        return None


IMAGE_PROVIDERS = [
    _gen_replicate,
    _gen_stability,
]


async def generate_image(prompt: str):
    for provider in IMAGE_PROVIDERS:
        log.info("Trying provider: %s", provider.__name__)
        img = await provider(prompt)
        if img:
            log.info("Provider %s succeeded", provider.__name__)
            return img
        log.info("Provider %s failed", provider.__name__)

    log.error("All image providers failed")
    return None


class ImageGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="img",
        description="Generate an AI image from a prompt",
    )
    @app_commands.describe(prompt="Describe the image you want")
    async def img(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(thinking=True)

        img_bytes = await generate_image(prompt)

        if not img_bytes:
            await interaction.followup.send("❌ Image generation failed.")
            return

        file = discord.File(io.BytesIO(img_bytes), filename="image.png")
        await interaction.followup.send(file=file)


async def setup(bot):
    await bot.add_cog(ImageGen(bot))
