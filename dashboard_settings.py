# dashboard_settings.py
import copy
import json
import os
import time

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


def guild_settings_key(guild_id: int | str) -> str:
    return f"fusbot:guild:{guild_id}:settings"


async def _redis_command(*parts):
    rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")

    if not rest_url or not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            rest_url.rstrip("/"),
            headers=headers,
            json=list(parts),
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("result")


async def get_guild_settings(guild_id: int | str):
    key = guild_settings_key(guild_id)
    now = time.time()

    cached = _CACHE.get(key)
    if cached and now - cached["time"] < _CACHE_TTL_SECONDS:
        return cached["settings"]

    raw = await _redis_command("GET", key)

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


async def save_guild_settings(guild_id: int | str, settings: dict):
    key = guild_settings_key(guild_id)
    merged = _deep_merge(DEFAULT_GUILD_SETTINGS, settings)

    await _redis_command("SET", key, json.dumps(merged))

    _CACHE[key] = {
        "time": time.time(),
        "settings": merged,
    }

    return merged


async def update_guild_setting(guild_id: int | str, section: str, key: str, value):
    settings = await get_guild_settings(guild_id)

    if section not in settings or not isinstance(settings[section], dict):
        settings[section] = {}

    settings[section][key] = value

    return await save_guild_settings(guild_id, settings)


async def guild_feature_enabled(
    guild_id: int | str | None,
    section: str,
    key: str,
    fallback: bool = True,
):
    if not guild_id:
        return fallback

    settings = await get_guild_settings(guild_id)
    return bool(settings.get(section, {}).get(key, fallback))


async def guard_interaction(interaction, section: str, key: str, label: str):
    if not interaction.guild:
        return True

    enabled = await guild_feature_enabled(interaction.guild.id, section, key)

    if enabled:
        return True

    message = f"{label} is disabled for this server in the dashboard."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)

    return False
