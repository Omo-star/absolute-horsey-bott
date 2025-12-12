import random
import time
import asyncio
import discord

REACT_PROBABILITY = 0.25
PASSIVE_REACT_PROBABILITY = 0.10
CHANNEL_REACT_COOLDOWN_SEC = 18
USER_REACT_COOLDOWN_SEC = 25
REPLY_DELAY_RANGE = (0.6, 2.2)
IGNORE_PREFIXES = ("!", "/", ".")

REACTIONS_GENERIC = ["👀", "👍", "💀", "😭", "🔥", "😂"]
REACTIONS_QUESTION = ["❓", "🤔"]

_last_channel_react = {}
_last_user_react = {}

def _now():
    return time.time()

def _on_cooldown(channel_id, user_id):
    t = _now()
    if t - _last_channel_react.get(channel_id, 0) < CHANNEL_REACT_COOLDOWN_SEC:
        return True
    if t - _last_user_react.get(user_id, 0) < USER_REACT_COOLDOWN_SEC:
        return True
    return False

def _mark_react(channel_id, user_id):
    t = _now()
    _last_channel_react[channel_id] = t
    _last_user_react[user_id] = t

async def maybe_react(message: discord.Message, mentioned: bool = False):
    if not message.guild:
        return
    if message.author.bot:
        return
    if message.content.startswith(IGNORE_PREFIXES):
        return
    if _on_cooldown(message.channel.id, message.author.id):
        return

    p = REACT_PROBABILITY if mentioned else PASSIVE_REACT_PROBABILITY
    if random.random() > p:
        return

    if "?" in message.content:
        emoji = random.choice(REACTIONS_QUESTION)
    else:
        emoji = random.choice(REACTIONS_GENERIC)

    try:
        await message.add_reaction(emoji)
        _mark_react(message.channel.id, message.author.id)
    except:
        pass

async def human_delay(channel: discord.abc.Messageable):
    delay = random.uniform(*REPLY_DELAY_RANGE)
    try:
        async with channel.typing():
            await asyncio.sleep(delay)
    except:
        await asyncio.sleep(delay)
