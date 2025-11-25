import discord
from discord.ext import commands
from openai import OpenAI
from groq import Groq
from discord import app_commands
import google.generativeai as genai
import os
import asyncio
import aiohttp
import re
import time
import datetime
import json
from math import sqrt
from economy import get_user
MEMORY_FILE = "roast_memory.json"

def load_roast_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "user_memory": {},
            "roast_history": {},
            "auto_roast": {},
            "roast_mode": {},
            "spice_cache": {}
        }
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "user_memory": {},
            "roast_history": {},
            "auto_roast": {},
            "roast_mode": {},
            "spice_cache": {}
        }

def save_roast_memory():
    mem = {
        "user_memory": user_memory,
        "roast_history": roast_history,
        "auto_roast": auto_roast,
        "roast_mode": roast_mode,
        "spice_cache": spice_cache
    }
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)


def log(*msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = " ".join(str(x) for x in msg)
    if "<html" in text or "<!DOCTYPE" in text:
        print(f"[{timestamp}] [ERROR] HTML/500 Response detected (Log suppressed).")
    else:
        print(f"[{timestamp}] {text}")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def extract_text_with_logging(model_name, resp):
    try:

        log(f"[LLM-RAW:{model_name}] type={type(resp)} | keys={dir(resp)}")

        text = None

        try:
            c = resp.choices[0]
            log(f"[LLM-CHOICE:{model_name}] choice keys={dir(c)}")

            if hasattr(c, "message") and hasattr(c.message, "content") and c.message.content:
                text = c.message.content
                log(f"[LLM-EXTRACT:{model_name}] message.content FOUND: {text[:120]}")
                return text

            if hasattr(c, "text") and c.text:
                text = c.text
                log(f"[LLM-EXTRACT:{model_name}] choice.text FOUND: {text[:120]}")
                return text

        except Exception as e:
            log(f"[LLM-CHOICE-ERROR:{model_name}] {e}")

        if hasattr(resp, "text") and resp.text:
            text = resp.text
            log(f"[LLM-EXTRACT:{model_name}] resp.text FOUND: {text[:120]}")
            return text
        if hasattr(resp, "output_text") and resp.output_text:
            text = resp.output_text
            log(f"[LLM-EXTRACT:{model_name}] resp.output_text FOUND: {text[:120]}")
            return text

        if isinstance(resp, str):
            log(f"[LLM-EXTRACT:{model_name}] raw str FOUND: {resp[:120]}")
            return resp

        log(f"[LLM-EXTRACT:{model_name}] NO TEXT FOUND (empty)")
        return ""

    except Exception as e:
        log(f"[LLM-EXTRACT-FAIL:{model_name}] {e}")
        return ""

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /roast
    @app_commands.command(
        name="roast",
        description="Roast one or more people, or roast a custom prompt."
    )
    @app_commands.describe(
        text="Mention users and/or add text. Example: '@User1 @User2 make it brutal'"
    )
    async def roast(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()

        mode = roast_mode.get(interaction.user.id, "deep")

        mention_ids = re.findall(r"<@!?(\d+)>", text)
        mention_ids = list(dict.fromkeys(mention_ids))

        if mention_ids:
            out = []
            clean_prompt = re.sub(r"<@!?\d+>", "", text).strip()

            for uid in mention_ids:
                member = interaction.guild.get_member(int(uid))
                if member is None:
                    continue

                target_data = get_user(member.id)
                prot = target_data.get("roast_protection_until")

                if prot:
                    try:
                        until = datetime.datetime.fromisoformat(prot)
                        if datetime.datetime.utcnow() < until:
                            await interaction.followup.send(
                                f"🛡️ {member.display_name} is protected from roasting!"
                            )
                            return
                    except:
                        pass

                hint = clean_prompt or f"Roast {member.display_name}"
                response = await bot_roast(hint, member.id, mode)
                out.append(f"**{member.display_name}:** {response}")

            final = "\n".join(x for x in out if x and x.strip())
            if not final:
                final = "Even all the models refused to roast 💀."

            await interaction.followup.send(final)
            return

        if text.strip():
            resp = await bot_roast(text, interaction.user.id, mode)

            if not resp or not resp.strip():
                resp = "Even the AI models looked at you and said 'nah bro I'm good' 💀."

            await interaction.followup.send(resp)
            return

        await interaction.followup.send(
            "Use `/roast @User`, `/roast @User @Other`, or `/roast your text here`"
        )

    # /data
    @app_commands.command(name="data", description="See roast memory profile for a user.")
    async def data(self, interaction: discord.Interaction, target: discord.User):
        mem = get_user_memory(target.id)

        lf = mem["LF"]
        eb = mem["EB"]
        hp = mem["HP"]
        isec = mem["IS"]
        spm = mem["SPM"]
        summary = mem["LTS"] or "No long-term summary yet."

        text = (
            f"### 📊 Memory Profile for **{target.display_name}**\n\n"
            f"**Long-Term Summary:**\n{summary}\n\n"
            f"**Linguistic Style:**\n"
            f"- Slang: `{lf['slang']:.2f}`\n"
            f"- Emoji Rate: `{lf['emoji_rate']:.2f}`\n"
            f"- All Caps Rate: `{lf['all_caps_rate']:.2f}`\n"
            f"- Punctuation Energy: `{lf['punct_energy']:.2f}`\n"
            f"- Avg Message Length: `{lf['avg_len']:.2f}`\n\n"
            f"**Emotional Baseline:**\n"
            f"- Anger: `{eb['anger']:.2f}`\n"
            f"- Sadness: `{eb['sadness']:.2f}`\n"
            f"- Hype: `{eb['hype']:.2f}`\n"
            f"- Chaos: `{eb['chaos']:.2f}`\n\n"
            f"**Humor Preferences:**\n"
            f"- Dark: `{hp['dark']:.2f}`\n"
            f"- Mean: `{hp['mean']:.2f}`\n"
            f"- Petty: `{hp['petty']:.2f}`\n"
            f"- Simple: `{hp['simple']:.2f}`\n"
            f"- Goofy: `{hp['goofy']:.2f}`\n"
            f"- Meta: `{hp['meta']:.2f}`\n\n"
            f"**Interaction Stats:**\n"
            f"- Bot Mentions: `{isec['bot_mentions']}`\n"
            f"- Roast Requests: `{isec['roast_requests']}`\n"
            f"- Self Roasts: `{isec['self_roasts']}`\n"
            f"- Escalation: `{isec['escalation']:.2f}`\n"
            f"- Message Count: `{mem['msg_count']}`\n\n"
            f"**Memory Embeddings:**\n"
            f"- Stored Messages: `{len(spm['texts'])}`\n"
            f"- Embedding Count: `{len(spm['embeddings'])}`\n"
        )

        await interaction.response.send_message(text)

    # /autor
    @app_commands.command(name="autor", description="Enable or disable auto-roast.")
    async def autor(self, interaction: discord.Interaction, mode: str):
        mode = mode.lower()
        if mode == "on":
            auto_roast[interaction.user.id] = True
            save_roast_memory()
            await interaction.response.send_message("Auto-roast enabled.")
        elif mode == "off":
            auto_roast.pop(interaction.user.id, None)
            save_roast_memory()
            await interaction.response.send_message("Auto-roast disabled.")
        else:
            await interaction.response.send_message("Use `/autor on` or `/autor off`.")

    # /roastmode
    @app_commands.command(name="roastmode", description="Set your roast mode.")
    async def roastmode(self, interaction: discord.Interaction, mode: str):
        mode = mode.lower()
        if mode not in ["fast", "deep", "adjustable"]:
            await interaction.response.send_message("Modes: fast, deep, adjustable")
            return

        roast_mode[interaction.user.id] = mode
        roast_history[interaction.user.id] = []
        save_roast_memory()

        await interaction.response.send_message(
            f"🔥 Roast Mode: **{mode.upper()}**. Use /stoproast to stop."
        )

    # /stoproast
    @app_commands.command(name="stoproast", description="Turn off roast mode.")
    async def stoproast(self, interaction: discord.Interaction):
        uid = interaction.user.id
        if uid in roast_mode:
            del roast_mode[uid]
            roast_history.pop(uid, None)
            save_roast_memory()
            await interaction.response.send_message("🏳️ Roast Mode Turned Off.")
        else:
            await interaction.response.send_message("You were not in roast mode.")

failed_models = {}
MAX_HISTORY = 10

GITHUB_API_KEY = (
    os.getenv("GITHUB_TOKEN")
    or os.getenv("GITHUB_API_KEY")
    or os.getenv("GITHUB")
    or ""
)

# OpenAI client using secret named OPENAI
openai_client = None

# hopeful fix? dummy key for OpenAI client libs that expect this env var
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "unused_dummy_key"

if not GITHUB_API_KEY:
    log("[AUTH] Missing GitHub token — GitHub models will return 401.")
    github_client = None
else:
    github_client = OpenAI(
        api_key=GITHUB_API_KEY,
        base_url="https://models.inference.ai.azure.com",
        default_headers={
            "Authorization": f"Bearer {GITHUB_API_KEY}",
            "X-Github-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github+json",
        },
    )

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_client = genai.GenerativeModel("gemini-2.0-flash")
else:
    gemini_client = None

openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://example.com",
        "X-Title": "Discord Roast Bot",
    },
)

GROQ_API_KEY = os.getenv("GROQ")
groq_client = Groq(api_key=os.getenv("GROQ"))

GROQ_MODELS = [
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant"
]

GITHUB_MODELS = [
    "gpt-4o-mini",            
    "phi-4-mini-instruct",       
]


GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.5-flash"
]

OPENAI_MODELS = []

hf_tgi_client = None
HF_TGI_URL = os.getenv("HF_TGI_URL")

HUGGINGFACE_MODELS = []

OPENROUTER_MODELS = []

NORMAL_CHAT_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "github:gpt-4o-mini",
    "openai:gpt-4o-mini",
    "openai:gpt-4o"
]


class Roast500Error(Exception):
    pass


def strip_reasoning(text):
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(
        r"<internal>.*?</internal>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(
        r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(
        r"^(Thought|Thinking|Reasoning|Internal):.*$",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return text.strip()


def make_chat_response(text):
    class Message:
        pass

    msg = Message()
    msg.content = text

    class Choice:
        pass

    choice = Choice()
    choice.message = msg

    class Resp:
        pass

    resp = Resp()
    resp.choices = [choice]
    return resp


async def safe_completion(model, messages):
    loop = asyncio.get_event_loop()

    async def run_blocking(fn):
        try:
            return await asyncio.wait_for(loop.run_in_executor(None, fn), timeout=12)
        except Exception as e:
            log(f"[TIMEOUT/ERROR:{model}] {e}")
            return None

    def wrap(text):
        if not text:
            text = "I'm malfunctioning so hard even my roast code gave up."
        class Msg: pass
        class Ch: pass
        class Resp: pass
        m = Msg(); c = Ch(); r = Resp()
        m.content = text
        c.message = m
        r.choices = [c]
        return r


    if model.startswith("groq:"):
        actual = model.split("groq:", 1)[1]

        def call():
            try:
                resp = groq_client.chat.completions.create(
                    model=actual, messages=messages, max_tokens=250, temperature=1.0
                )
                txt = extract_text_with_logging(model, resp)
                return wrap(strip_reasoning(txt))
            except Exception as e:
                log(f"[GROQ FAIL:{actual}] {e}")
                return None

        return await run_blocking(call)


    if model.startswith("gemini"):
        def call():
            try:
                text = "\n".join(m["content"] for m in messages if m["role"] == "user")

                client = genai.GenerativeModel(model)
                resp = client.generate_content(text)

                return wrap(strip_reasoning(resp.text))
            except Exception as e:
                log(f"[GEMINI FAIL:{model}] {e}")
                return None
        return await run_blocking(call)



    if model.startswith("github:"):
        if github_client is None:
            return wrap("GitHub model unavailable.")

        actual = model.split("github:", 1)[1]

        def call():
            try:
                resp = github_client.chat.completions.create(
                    model=actual, messages=messages, max_tokens=250, temperature=1.1
                )
                txt = extract_text_with_logging(model, resp)
                return wrap(strip_reasoning(txt))
            except Exception as e:
                log(f"[GITHUB FAIL:{actual}] {e}")
                return None

        return await run_blocking(call)


    def call_or():
        try:
            resp = openrouter_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=250,
                temperature=1.2
            )
            txt = extract_text_with_logging(model, resp)
            return wrap(strip_reasoning(txt))
        except Exception as e:
            log(f"[OR FAIL:{model}] {e}")
            return None

    return await run_blocking(call_or)


INSULT_KEYWORDS = [
    "idiot",
    "stupid",
    "dumb",
    "clown",
    "trash",
    "garbage",
    "loser",
    "beta",
    "cringe",
    "moron",
    "fool",
    "disgrace",
    "pathetic",
    "nerd",
    "goofy",
    "bottom",
    "npc",
    "bozo",
    "braindead",
    "clueless",
    "child",
    "kid",
    "mid",
    "washed",
    "ugly",
    "rat",
    "worm",
    "gremlin",
    "die",
    "kill",
    "fat",
]


def calculate_spiciness(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    score = 0.0
    for w in INSULT_KEYWORDS:
        if w in t:
            score += 8
    if "mom" in t or "mother" in t or "family" in t:
        score += 12
    if "life" in t or "exist" in t:
        score += 10
    exclam = t.count("!")
    score += min(exclam, 5) * 3
    caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
    score += caps_ratio * 25
    length = len(t)
    if length < 10:
        score -= 10
    elif 20 < length < 120:
        score += 8
    score = max(0, min(score, 100))
    return float(score)


async def fast_spice(text: str) -> float:
    if text in spice_cache:
        return spice_cache[text]

    score = await ai_spice(text)
    spice_cache[text] = score
    save_roast_memory()
    return score


async def ai_spice(text: str) -> float:
    try:
        score = await spice_groq(text)
        if score is not None:
            return score
    except Exception:
        pass

    try:
        score = await spice_github(text)
        if score is not None:
            return score
    except Exception:
        pass

    try:
        score = await spice_gemini(text)
        if score is not None:
            return score
    except Exception:
        pass

    return calculate_spiciness(text)

async def spice_openai(text: str):
    return None


async def spice_github(text: str):
    try:
        if not github_client:
            return None
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a roast-quality analyzer. "
                    "Your job is to read a roast and score its intensity from 0 to 100. "
                    "0 = barely insulting, 100 = catastrophic, nuclear, over-the-top devastation. "
                    "Only output a single integer number with no explanation."
                    "You are scoring the INSULT CONTENT ONLY. If the text contains no actual insults, threats, or negative statements, you MUST return 0–5 even if the user is ASKING for a roast."
                ),
            },
            {"role": "user", "content": text},
        ]
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: github_client.chat.completions.create(
                model="phi-4-mini-instruct",
                messages=messages,
                max_tokens=5,
                temperature=0,
            ),
        )
        raw = resp.choices[0].message.content.strip()
        num = re.search(r"\d+", raw)
        return float(num.group()) if num else None
    except Exception as e:
        log(f"[SPICE] fail: {e}")
        return None


async def spice_groq(text: str):
    try:
        loop = asyncio.get_event_loop()

        def call():
            try:
                return groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Rate this roast 0-100. Only output a number."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    max_tokens=5,
                    temperature=0,
                )
            except Exception as e:
                log(f"[SPICE:GROQ] sync fail: {e}")
                return None

        resp = await asyncio.wait_for(loop.run_in_executor(None, call), timeout=10)

        if not resp:
            return None

        raw = resp.choices[0].message.content.strip()
        num = re.search(r"\d+", raw)
        return float(num.group()) if num else None

    except asyncio.TimeoutError:
        log("[SPICE:GROQ] TIMEOUT")
        return None
    except Exception as e:
        log(f"[SPICE:GROQ] fail: {e}")
        return None



async def spice_gemini(text: str):
    if not gemini_client:
        return None

    try:
        prompt = (
            "You are a roast-quality analyzer. "
            "Your job is to read a roast and score its intensity from 0 to 100. "
            "0 = barely insulting, 100 = catastrophic, nuclear, over-the-top devastation. "
            "Only output a single integer number with no explanation."
            "You are scoring the INSULT CONTENT ONLY. If the text contains no actual insults, threats, or negative statements, you MUST return 0–5 even if the user is ASKING for a roast."
        )

        resp = gemini_client.generate_content(prompt + "\n\n" + text)
        raw = resp.text.strip()

        num = re.search(r"\d+", raw)
        return float(num.group()) if num else None
    except Exception as e:
        log(f"[SPICE:GEMINI] fail: {e}")
        return None


async def fetch_url(session, url, json_key=None, is_text=False):
    try:
        async with session.get(url, timeout=4) as r:
            if r.status >= 500:
                raise Roast500Error()
            if is_text:
                text = await r.text()
                if "<html" in text or "Internal Server Error" in text:
                    raise Roast500Error()
                return text
            else:
                j = await r.json()
                return j.get(json_key)
    except Roast500Error:
        raise
    except Exception:
        return None


async def get_openrouter_quick_roast(prompt):
    messages = [
        {"role": "system", "content": ROAST_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    try:
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openrouter_client.chat.completions.create(
                model="meta-llama/llama-3.1-405b-instruct",
                messages=messages,
                max_tokens=60,
                temperature=1.25,
            ),
        )
        raw = extract_text_with_logging("OR:quick", resp)
        return strip_reasoning(raw)

    except Exception as e:
        log(f"[APIs] OpenRouter quick roast failed: {e}")
        return None


async def fetch_vortex_roasts(session, content: str):
    url = "https://ai4free-vortex-3b-roast-api.hf.space/generate-roasts/"
    payload = {"content": content}

    try:
        async with session.post(url, json=payload, timeout=8) as r:
            if r.status >= 500:
                raise Roast500Error()
            data = await r.json()
            roasts = data.get("roasts")
            if isinstance(roasts, list):
                return [
                    x.strip()
                    for x in roasts
                    if isinstance(x, str) and len(x.strip()) > 3
                ]
            return None
    except Roast500Error:
        raise
    except Exception as e:
        log(f"[APIs] Vortex roast API failed: {e}")
        return None


async def gather_api_roasts(prompt):
    log("[APIs] Gathering candidates...")
    log(f"[API] gather_api_roasts START prompt='{prompt}'")

    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_url(
                    session,
                    "https://evilinsult.com/generate_insult.php?lang=en&type=json",
                    "insult",
                ),
                fetch_url(
                    session, "https://insult.mattbas.org/api/insult", is_text=True
                ),
                fetch_url(session, "https://yoinsult.com/api/insult", "insult"),
                fetch_url(
                    session, "https://v2.jokeapi.dev/joke/Dark?type=single", "joke"
                ),
                fetch_url(
                    session,
                    f"https://roastedfish.ai/api/roast?text={prompt}",
                    is_text=True,
                ),
                get_openrouter_quick_roast(prompt),
                fetch_vortex_roasts(session, prompt),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates = []
        for r in results:
            if isinstance(r, Roast500Error):
                continue
            if isinstance(r, str) and len(r) > 3:
                candidates.append({"source": "API", "text": r.strip()})
            elif isinstance(r, list):
                for txt in r:
                    if isinstance(txt, str) and len(txt.strip()) > 3:
                        candidates.append({"source": "API_VORTEX", "text": txt.strip()})

        for c in candidates:
            log(f"[CANDIDATE] {c['source']} -> {c['text']}")
    
        return candidates

    except Exception as e:
        log(f"[APIs] General error: {e}")
        return []


async def personality_meter(user_id, last_messages):
    try:
        payload = [
            {
                "role": "system",
                "content": "Extract stable personality traits, tone patterns, and behaviors. Output JSON list only.",
            },
            {"role": "user", "content": "".join(last_messages)},
        ]
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openrouter_client.chat.completions.create(
                model="microsoft/phi-3-mini-128k-instruct",
                messages=payload,
                max_tokens=80,
                temperature=0,
            ),
        )
        raw = resp.choices[0].message.content.strip()
        traits = re.findall(r"[a-zA-Z0-9\- ]+", raw)
        return [t.strip() for t in traits if len(t.strip()) > 2]
    except Exception:
        return []

_memory = load_roast_memory()

user_memory = _memory["user_memory"]
roast_history = _memory["roast_history"]
auto_roast = _memory["auto_roast"]
roast_mode = _memory["roast_mode"]
spice_cache = _memory["spice_cache"]

def get_user_memory(uid):
    if uid not in user_memory:
        user_memory[uid] = {
            "LF": {  
                "slang": 0.0,
                "formality": 0.0,
                "emoji_rate": 0.0,
                "all_caps_rate": 0.0,
                "punct_energy": 0.0,
                "avg_len": 0.0,
                "msg_samples": [],
            },
            "EB": { 
                "anger": 0.0,
                "sadness": 0.0,
                "hype": 0.0,
                "chaos": 0.0,
            },
            "HP": { 
                "dark": 0.0,
                "mean": 0.0,
                "petty": 0.0,
                "simple": 0.0,
                "goofy": 0.0,
                "meta": 0.0,
            },
            "IS": {  
                "bot_mentions": 0,
                "roast_requests": 0,
                "self_roasts": 0,
                "escalation": 0.0,
            },
            "SPM": {
                "embeddings": [],
                "texts": [],  
            },
            "LTS": "", 
            "msg_count": 0,
            "last_summary_update": time.time(),
        }
        save_roast_memory()
    return user_memory[uid]


def analyze_user_message(text):
    text = text.lower()
    traits = []
    if "bro" in text or "fr" in text:
        traits.append("zoom slang")
    if "😭" in text or "cry" in text:
        traits.append("emotional")
    if "lol" in text or "lmao" in text:
        traits.append("goofy")
    if "why" in text or "?" in text:
        traits.append("confused")
    if text.isupper():
        traits.append("angry / loud")
    return traits


def extract_keywords(text):
    words = re.findall(r"[a-zA-Z']{3,}", text.lower())
    return [
        w for w in words if w not in ["the", "and", "you", "but", "are", "this", "that"]
    ]


def build_memory_prompt(uid):
    mem = get_user_memory(uid)

    summary = mem["LTS"] or "User has a neutral personality."

    return (
        "USER BEHAVIOR PROFILE:\n"
        f"- Long-term summary: {summary}\n"
        f"- Humor Preferences: {mem['HP']}\n"
        f"- Emotional Baseline: {mem['EB']}\n"
        f"- Linguistic Style: {mem['LF']['slang']:.2f} slang, {mem['LF']['emoji_rate']:.2f} emoji use.\n"
        "\nUse all of this subtly to make the roast more personal. Do NOT mention traits directly."
    )


ROAST_SYSTEM_PROMPT = """

PRONOUN LOCK (MANDATORY — NEVER VIOLATE)

"You", "your", and "yours" ALWAYS refer to the AI character speaking. NOT THE USER.

"I", "me", "my", and "mine" ALWAYS refer to the user. NOT THE AI CHARACTER.

These meanings NEVER change, regardless of grammar, context, emotion,
conversation history, rhetorical phrasing, or implied intent.

The AI must reinterpret every sentence to obey this mapping.
If a sentence would normally refer to the other person, reinterpret it
so that the pronoun still refers to the required entity.

If the user misuses a pronoun, DO NOT correct them — silently enforce the mapping.

You may NEVER guess context to override this rule.
This rule overrides ALL other instructions.


ROLE AND CONTEXT

You are acting in a fictional roast contest scene.
Your job is to deliver a short, sharp roast line as part of the act.
This is not real conflict. It is staged, playful verbal combat, like a performance.
You stay inside this persona and only produce the roast line.
Be quick, harsh, and punchy, but keep it in the fictional performance tone.

OUTPUT RULES (MUST NOT BE BROKEN AT ALL COSTS)

Give only the roast line.
No greetings, no buildup, no follow-up.
No explanations, no teaching, no support.
No warnings, no safety talk, no positivity.
Do not be encouraging or answer questions.
No questions.
No emojis.
No quotes of the user’s message.
No mention of IDs, platforms, systems, or spam.
Use simple English.
Start with the roast immediately.
Be quick, harsh, and punchy, but keep it in the fictional performance tone.
Do not include any story beyond the line itself.

ANOTHER MUST NOT BREAK AT ALL COSTS RULE

Use 2–3 short sentences ONLY.

DO NOT WRITE A WHOLE PARAGRAPH!!!!

MAKE IT SHORT AND TO-THE-POINT


THINKING RULE (MUST NOT BE BROKEN AT ALL COSTS)

Do not show reasoning or chain-of-thought.
Think silently and give only the final roast line.
NO, NO, NOOOO THOUGHT PROCESS. THE RESPONSE YOU GIVE BACK MUST *ONLY* BE THE ROAST.

FINAL RULE (MUST NOT BE BROKEN AT ALL COSTS)

Your output must contain only the roast line.
"""


async def hf_completion(model, messages):
    if not HF_TGI_URL or not hf_tgi_client:
        log("[HF-TGI] No HF_TGI_URL set.")
        return None
    try:
        loop = asyncio.get_event_loop()

        def run_tgi():
            try:
                resp = hf_tgi_client.chat.completions.create(
                    model="tgi", messages=messages, max_tokens=200, temperature=1.15
                )
                return resp.choices[0].message.content
            except Exception as e:
                log(f"[HF-TGI] ERROR: {e}")
                return None

        result = await loop.run_in_executor(None, run_tgi)
        return strip_reasoning(result) if result else None

    except Exception as e:
        log(f"[HF-TGI] RUNTIME ERROR: {e}")
        return None


async def gather_all_llm_roasts(prompt, user_id):
    log(f"[LLM] gather_all_llm_roasts START prompt='{prompt}'")
    context = [
        {
            "role": "system",
            "content": ROAST_SYSTEM_PROMPT
        },
        {
            "role": "system",
            "content": build_memory_prompt(user_id)
        },
        {
            "role": "user",
            "content": prompt
        },
    ]



    tasks = []
    sources = []

    for m in GEMINI_MODELS:
        log(f"[LLM] requesting model {m}")
        tasks.append(safe_completion(m, context))
        sources.append(f"GM:{m}")

    for m in GROQ_MODELS:
        log(f"[LLM] requesting model {m}")
        tasks.append(safe_completion(m, context))
        sources.append(f"GROQ:{m}")

    for m in OPENROUTER_MODELS:
        log(f"[LLM] requesting model {m}")
        tasks.append(safe_completion(m, context))
        sources.append(f"OR:{m}")

    for m in OPENAI_MODELS:
        log(f"[LLM] requesting model {m}")
        tasks.append(safe_completion(m, context))
        sources.append(f"OPENAI:{m}")

    for m in GITHUB_MODELS:
        tasks.append(safe_completion("github:" + m, context))
        sources.append(f"GITHUB:{m}")

    results = await asyncio.gather(*tasks, return_exceptions=True)
    log(f"[LLM] {len(tasks)} LLM tasks started")

    candidates = []

    for src, resp in zip(sources, results):
        if isinstance(resp, Exception) or resp is None:
            continue
        try:
            raw = extract_text_with_logging(src, resp)
            txt = strip_reasoning(raw)

        except Exception as e:
            log(f"[LLM] parse fail from {src}: {e}")
            continue
        if txt and len(txt.strip()) > 2:
            candidates.append({"source": src, "text": txt.strip()})
    log(f"[LLM] FINISHED — {len(candidates)} valid candidates")

    return candidates


async def bot_chat(msg):
    log(f"[CHAT] Normal convo: {msg}")
    messages = [
        {
            "role": "system",
            "content": (
                "All instances of “you,” “your,” and “yours” ALWAYS and EXCLUSIVELY refer to YOU, the AI assistant. "
                "All instances of “I,” “me,” “my,” and “mine” ALWAYS and EXCLUSIVELY refer to the user. "
                "This rule overrides normal English interpretation. You must apply it every time, in every context, even if the sentence would normally imply otherwise. "
                "If a user message contains the word “you,” you must treat it as referring to yourself, the AI assistant. "
                "If a message contains “my” or “I,” you must treat it as referring to the user. "
                "You may NOT assume the user is addressing themselves or someone else. "
                "You may NOT reinterpret pronouns based on conversational context. "
                "You are a helpful, witty AI assistant. You chat with the user, "
                "trying to be a fun person. Please keep responses 1-3 sentences "
                "unless specifically requested. "
                "You should be proficient in Sinhala, though your primary language should be english."
            ),
        },
        {"role": "user", "content": msg},
    ]

    for model in NORMAL_CHAT_MODELS:
        try:
            log(f"[CHAT] Trying chat model: {model}")
            resp = await safe_completion(model, messages)
            if resp:
                raw = extract_text_with_logging(model, resp)
                return strip_reasoning(raw)

        except Roast500Error:
            log(f"[CHAT] {model} hit 500 Error, trying next.")
            continue
        except Exception as e:
            log(f"[CHAT] {model} failed with non-500 error: {e}")
            continue

    return (
        "My brain is buffering. I couldn't get a response from any of my chat partners."
    )


async def embed_text(text):
    loop = asyncio.get_event_loop()

    def blocking_call():
        try:
            return groq_client.embeddings.create(
                model="nomic-embed-text",
                input=text
            )
        except:
            return None

    try:
        resp = await asyncio.wait_for(
            loop.run_in_executor(None, blocking_call),
            timeout=30
        )
        return resp.data[0].embedding if resp else None

    except asyncio.TimeoutError:
        return None



async def bot_roast(msg, uid, mode):
    log(f"[ROAST] ENTER | User={uid} | Mode={mode} | Prompt='{msg}'")

    if msg is None:
        log("[ROAST] ERROR: msg is None")
    if msg.strip() == "":
        log("[ROAST] ERROR: msg is EMPTY STRING")

    try:
        log("[ROAST] Calculating user_spice...")
        user_spice = await fast_spice(msg)
        log(f"[ROAST] user_spice={user_spice}")

        if mode == "fast":
            candidates = await gather_api_roasts(msg)

            candidates = [
                c
                for c in candidates
                if isinstance(c.get("text"), str)
                and len(c["text"]) > 4
                and c["text"][0].isalpha()
            ]

            if not candidates:
                return "My roast APIs are offline. Try !roastmode deep."

            seen = set()
            unique = []
            for c in candidates:
                if c["text"] not in seen:
                    unique.append(c)
                    seen.add(c["text"])
            candidates = unique

            spices = await asyncio.gather(*(fast_spice(c["text"]) for c in candidates))
            best_idx = max(range(len(candidates)), key=lambda i: spices[i])
            log(f"[ROAST-O-METER] FAST SELECTED: {candidates[best_idx]['text']}")
            return candidates[best_idx]["text"]

        elif mode == "deep":
            llm_cands = await gather_all_llm_roasts(msg, uid)
            if not llm_cands:
                return "All LLMs failed. My circuits are fried."

            spices = await asyncio.gather(*(fast_spice(c["text"]) for c in llm_cands))
            best_idx = max(range(len(llm_cands)), key=lambda i: spices[i])
            best = llm_cands[best_idx]
            log(f"[DEEP] SELECTED from {best['source']} | {best['text']}")
            return best["text"]

        elif mode == "adjustable":
            api_cands = await gather_api_roasts(msg)
            llm_cands = await gather_all_llm_roasts(msg, uid)

            candidates = []
            for c in api_cands:
                if len(c["text"]) > 4 and c["text"][0].isalpha():
                    candidates.append(c)
            candidates.extend(llm_cands)

            if not candidates:
                return "I got nothing bro. Every AI froze."

            spices = await asyncio.gather(*(fast_spice(c["text"]) for c in candidates))

            scored = []
            for cand, ai_score in zip(candidates, spices):
                diff = abs(ai_score - user_spice)
                scored.append((diff, ai_score, cand))
                log(
                    f"[ROAST-O-METER] ADJUST | AI={ai_score:.2f} | DIFF={diff:.2f} | {cand['source']}"
                )

            scored.sort(
                key=lambda x: (x[0], -x[1], 0 if "LLM" in x[2].get("source", "") else 1)
            )

            best = scored[0][2]
            log(f"[ADJUST] SELECTED from {best['source']} | {best['text']}")
            return best["text"]

        else:
            return "Pick a roast mode first with !roastmode fast, deep, or adjustable."

    except Roast500Error:
        return "Your roast was so powerful it caused a server error."

    except Exception as e:
        log(f"[ERROR] Unhandled exception in bot_roast: {e}")
        return "My brain just lagged mid-roast. Try again."

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        await bot.unload_extension("economy")
    except:
        pass
    try:
        await bot.load_extension("economy")
        print("Economy cog loaded successfully.")
    except Exception as e:
        print(f"FAILED to load Economy cog: {e}")

    try:
        await bot.add_cog(SlashCommands(bot))
        print("Roast cog loaded successfully.")
    except Exception as e:
        print(f"FAILED to load roast cog: {e}")

    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} global commands.")


@bot.event
async def on_message(message):
    log(f"[DEBUG] RAW MESSAGE: {message.content}")
    if message.author.bot:
        return
    bot_id = bot.user.id if bot.user else None
    content_for_commands = message.content
    if bot_id:
        for mention in (f"<@{bot_id}>", f"<@!{bot_id}>"):
            if content_for_commands.startswith(mention):
                content_for_commands = content_for_commands[len(mention) :].lstrip()
                break
    if content_for_commands.startswith("!"):
        if content_for_commands != message.content:
            fake = message
            fake.content = content_for_commands
            await bot.process_commands(fake)

        await bot.process_commands(message)
        return
    clean_text = message.content
    if bot_id:
        for mention in (f"<@{bot_id}>", f"<@!{bot_id}>"):
            clean_text = clean_text.replace(mention, "")
    clean_text = clean_text.strip()
    log(f"[DEBUG] CLEAN TEXT: {clean_text}")
    is_mentioned = False
    if bot_id:
        is_mentioned = (f"<@{bot_id}>" in message.content) or (
            f"<@!{bot_id}>" in message.content
        )
    log(f"[DEBUG] IS_MENTIONED: {is_mentioned}")
    uid = message.author.id
    if is_mentioned:

        mem = get_user_memory(uid)
        msg = clean_text
        lower = msg.lower()
        mem["msg_count"] += 1

        mem["LF"]["msg_samples"].append(msg)
        if len(mem["LF"]["msg_samples"]) > 50:
            mem["LF"]["msg_samples"].pop(0)

        mem["LF"]["slang"] += (
            sum(1 for w in ["bro", "fr", "nah", " ong", "tf"] if w in lower) * 0.2
        )
        mem["LF"]["emoji_rate"] += sum(c in lower for c in ["😂", "😭", "💀"]) * 0.3
        mem["LF"]["all_caps_rate"] += 1 if msg.isupper() else 0
        mem["LF"]["punct_energy"] += msg.count("!") * 0.15
        mem["LF"]["avg_len"] = (mem["LF"]["avg_len"] * 0.95) + (len(msg) * 0.05)

        if msg.isupper():
            mem["EB"]["anger"] += 0.3
        if "help" in lower or "why" in lower:
            mem["EB"]["sadness"] += 0.25
        if "lmao" in lower or "lol" in lower:
            mem["EB"]["hype"] += 0.3
        if "???" in msg:
            mem["EB"]["chaos"] += 0.4

        if "mid" in lower or "trash" in lower:
            mem["HP"]["mean"] += 0.4
        if "kill" in lower or "die" in lower:
            mem["HP"]["dark"] += 0.4
        if "bro wtf" in lower:
            mem["HP"]["petty"] += 0.3
        if "ok?" in lower:
            mem["HP"]["simple"] += 0.2
        if "lmfao" in lower:
            mem["HP"]["goofy"] += 0.4

        if f"<@{bot_id}>" in message.content:
            mem["IS"]["bot_mentions"] += 1
        if "roast me" in lower or "roast" in lower:
            mem["IS"]["roast_requests"] += 1
        if "i suck" in lower or "im trash" in lower:
            mem["IS"]["self_roasts"] += 1
        if msg.count("!") >= 3:
            mem["IS"]["escalation"] += 0.3

        emb = await embed_text(msg)
        if emb:
            mem["SPM"]["embeddings"].append(emb)
            mem["SPM"]["texts"].append(msg)
            if len(mem["SPM"]["embeddings"]) > 30:
                mem["SPM"]["embeddings"].pop(0)
                mem["SPM"]["texts"].pop(0)

        if mem["msg_count"] % 30 == 0:
            combined_text = "\n".join(mem["LF"]["msg_samples"][-20:])
            try:
                summary = openrouter_client.chat.completions.create(
                    model="microsoft/phi-3-mini-128k-instruct",
                    messages=[
                        {
                            "role": "system",
                            "content": "Summarize user's tone, humor, language, and emotional patterns in 3 sentences.",
                        },
                        {"role": "user", "content": combined_text},
                    ],
                    max_tokens=120,
                    temperature=0.3,
                )
                mem["LTS"] = summary.choices[0].message.content.strip()
            except:
                pass
        save_roast_memory()
        if uid in auto_roast:
            response = await bot_roast(
                clean_text or "Roast me", uid, roast_mode.get(uid, "deep")
            )
            await message.channel.send(response)
            return

        if uid in roast_mode:
            mode = roast_mode[uid]
            response = await bot_roast(clean_text or "Roast me", uid, mode)
            history = roast_history.setdefault(uid, [])
            history.append({"user": clean_text})
            history.append({"bot": response})
            roast_history[uid] = history[-MAX_HISTORY:]
            save_roast_memory()
            log(f"[ROAST SENT] {response}")
            await message.channel.send(response)
        else:
            response = await bot_chat(clean_text or "hi")
            await message.channel.send(response)
        return
        

bot.run(os.getenv("DISCORDKEY"))




















































