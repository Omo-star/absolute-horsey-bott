import copy
import json
import os
import time
from urllib.parse import quote

import aiohttp

DEFAULT_GUILD_SETTINGS = {
    "setup": {
        "starterGuide": True,
        "setupPost": True,
        "permissionsCheck": True,
        "onboardingRoutes": True,
    },
    "economy": {
        "dailyRewards": True,
        "shopAccess": True,
        "stocksMarket": True,
        "leaderboards": True,
    },
    "ai": {
        "roastMode": True,
        "autoRoast": False,
        "aiMemory": True,
        "codeTools": True,
    },
    "automod": {
        "spamFilter": True,
        "slurFilter": True,
        "punishments": False,
        "settingsAudit": True,
    },
    "activityIntensity": 84,
}

_CACHE = {}
_CACHE_TTL_SECONDS = 10


def _deep_merge(defaults, incoming):
    output = copy.deepcopy(defaults)

    if not isinstance(incoming, dict):
        return output

    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(output.get(key), dict):
            output[key] = _deep_merge(output[key], value)
        else:
            output[key] = value

    return output


def _settings_key(guild_id: int | str) -> str:
    return f"fusbot:guild:{guild_id}:settings"


async def _redis_get(key: str):
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if not rest_url or not token:
        return None

    url = f"{rest_url.rstrip('/')}/get/{quote(key, safe='')}"
    headers = {"Authorization": f"Bearer {token}"}

    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("result")


async def get_guild_settings(guild_id: int | str):
    key = _settings_key(guild_id)
    now = time.time()

    cached = _CACHE.get(key)
    if cached and now - cached["time"] < _CACHE_TTL_SECONDS:
        return cached["settings"]

    raw = await _redis_get(key)

    if not raw:
        settings = copy.deepcopy(DEFAULT_GUILD_SETTINGS)
    else:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            settings = _deep_merge(DEFAULT_GUILD_SETTINGS, parsed)
        except Exception:
            settings = copy.deepcopy(DEFAULT_GUILD_SETTINGS)

    _CACHE[key] = {
        "time": now,
        "settings": settings,
    }

    return settings
