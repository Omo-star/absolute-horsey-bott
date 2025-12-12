import random
import time
import asyncio
import discord
import re

REACT_PROBABILITY = 0.35
PASSIVE_REACT_PROBABILITY = 0.12

CHANNEL_REACT_COOLDOWN_SEC = 22
USER_REACT_COOLDOWN_SEC = 30

BASE_DELAY = (0.35, 1.0)
PER_CHAR_DELAY = 0.018

IGNORE_PREFIXES = ("!", "/", ".")

REACTIONS_ACK = ["👍", "👌"]
REACTIONS_SEE = ["👀"]
REACTIONS_FUNNY = ["😂", "😭", "💀"]
REACTIONS_HYPE = ["🔥", "💯", "🚀"]
REACTIONS_QUESTION = ["❓", "🤔"]
REACTIONS_SAD = ["😔", "🫂"]

LOW_EFFORT = {
    "hi", "hey", "hello", "yo", "sup", "ok", "okay", "k", "lol", "lmao", "nah", "bruh"
}

FUNNY_KEYS = ["lol", "lmao", "lmfao", "😭", "😂", "💀", "wtf", "bro"]
HYPE_KEYS = ["lets go", "fire", "goat", "insane", "crazy", "holy"]
SAD_KEYS = ["sad", "tired", "upset", "cry", "depressed", "pain"]
ACK_KEYS = ["thanks", "thx", "got it", "ok cool"]

_last_channel_react = {}
_last_user_react = {}

def _now():
    return time.time()

def _cooldown(channel_id, user_id):
    t = _now()
    if t - _last_channel_react.get(channel_id, 0) < CHANNEL_REACT_COOLDOWN_SEC:
        return True
    if t - _last_user_react.get(user_id, 0) < USER_REACT_COOLDOWN_SEC:
        return True
    return False

def _mark(channel_id, user_id):
    t = _now()
    _last_channel_react[channel_id] = t
    _last_user_react[user_id] = t

def _norm(text):
    return re.sub(r"\s+", " ", text.lower().strip())

def _low_effort(text):
    t = _norm(text)
    return len(t) <= 4 or t in LOW_EFFORT

def _has(text, keys):
    t = text.lower()
    return any(k in t for k in keys)

async def maybe_react(message: discord.Message, mentioned: bool = False):
    if not message.guild:
        return
    if message.author.bot:
        return
    if message.content.startswith(IGNORE_PREFIXES):
        return
    if _cooldown(message.channel.id, message.author.id):
        return

    content = message.content.strip()
    if not content or _low_effort(content):
        return

    p = REACT_PROBABILITY if mentioned else PASSIVE_REACT_PROBABILITY
    p += min(len(content) / 200, 0.25)

    if random.random() > p:
        return

    text = content.lower()

    if "?" in content and len(content) > 10:
        emoji = random.choice(REACTIONS_QUESTION)
    elif _has(text, SAD_KEYS):
        emoji = random.choice(REACTIONS_SAD)
    elif _has(text, FUNNY_KEYS):
        emoji = random.choice(REACTIONS_FUNNY)
    elif _has(text, HYPE_KEYS):
        emoji = random.choice(REACTIONS_HYPE)
    elif _has(text, ACK_KEYS):
        emoji = random.choice(REACTIONS_ACK)
    elif len(content) > 80:
        emoji = random.choice(REACTIONS_SEE)
    else:
        emoji = random.choice(REACTIONS_ACK + REACTIONS_SEE)

    try:
        await message.add_reaction(emoji)
        _mark(message.channel.id, message.author.id)
    except:
        pass

async def human_delay(channel: discord.abc.Messageable, reply_text: str = ""):
    length = len(reply_text)

    base = random.uniform(0.4, 1.0)
    per_char = random.uniform(0.012, 0.02)
    total = base + min(length * per_char, 4.5)

    chunks = max(1, int(total / 1.4))
    remaining = total

    for i in range(chunks):
        slice_delay = min(remaining, random.uniform(0.8, 1.6))
        remaining -= slice_delay
        try:
            async with channel.typing():
                await asyncio.sleep(slice_delay)
        except:
            await asyncio.sleep(slice_delay)

        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(0.2, 0.6))

