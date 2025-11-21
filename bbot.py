import discord
from discord.ext import commands
from openai import OpenAI
from groq import Groq
import google.generativeai as genai
import os
import asyncio
import aiohttp
import re
import time
import datetime

def log(*msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = " ".join(str(x) for x in msg)
    if "<html" in text or "<!DOCTYPE" in text:
        print(f"[{timestamp}] [ERROR] HTML/500 Response detected (Log suppressed).")
    else:
        print(f"[{timestamp}] {text}")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

auto_roast = {}

roast_history = {}
failed_models = {}
roast_mode = {}
MAX_HISTORY = 10

spice_cache = {}


GITHUB_API_KEY = (
    os.getenv("GITHUB_TOKEN")
    or os.getenv("GITHUB_API_KEY")
    or os.getenv("GITHUB")
    or ""
)

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
            "Accept": "application/vnd.github+json"
        }
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
        "X-Title": "Discord Roast Bot"
    }
)


GROQ_API_KEY = os.getenv("GROQ")
groq_client = Groq(api_key=os.getenv("GROQ"))

GROQ_MODELS = [
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

GITHUB_MODELS = [
    "gpt-4o-mini",
    "llama-3.3-70b-instruct",
    "phi-4-mini-instruct",
]


GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
]

hf_tgi_client = None
HF_TGI_URL = os.getenv("HF_TGI_URL")

HUGGINGFACE_MODELS = []

OPENROUTER_MODELS = [
    "openai/gpt-3.5-turbo"
]

NORMAL_CHAT_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "github:gpt-4o-mini",
    "github:llama-3.3-70b-instruct"
]

class Roast500Error(Exception):
    pass

def strip_reasoning(text):
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<internal>.*?</internal>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"^(Thought|Thinking|Reasoning|Internal):.*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
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

    # new prefix handling !
    if model.startswith("groq:"):
        actual = model.split("groq:", 1)[1]
        def call():
            try:
                resp = groq_client.chat.completions.create(
                    model=actual,
                    messages=messages,
                    max_tokens=300,
                    temperature=1.1
                )
                return make_chat_response(resp.choices[0].message.content)
            except Exception as e:
                log(f"[GROQ ERROR:{actual}] {e}")
                return None
        return await loop.run_in_executor(None, call)

    if model.startswith("github:"):
        if github_client is None:
            log("[GITHUB] Skipping GitHub model — no valid API key.")
            return None
        actual = model.split("github:", 1)[1]
        def call():
            try:
                resp = github_client.chat.completions.create(
                    model=actual,
                    messages=messages,
                    max_tokens=300,
                    temperature=1.1
                )
                return make_chat_response(resp.choices[0].message.content)
            except Exception as e:
                log(f"[GITHUB ERROR:{actual}] {e}")
                return None
        return await asyncio.get_event_loop().run_in_executor(None, call)

    # add gemini to models
    if model.startswith("gemini"):
        if not gemini_client:
            return None
        try:
            user_input = "\n".join(m["content"] for m in messages if m["role"] == "user")
            resp = gemini_client.generate_content(user_input)
            return make_chat_response(resp.text)
        except Exception as e:
            log(f"[GEMINI ERROR] {e}")
            return None

    if model in GROQ_MODELS:
        def call():
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=300,
                    temperature=1.1
                )
                return make_chat_response(resp.choices[0].message.content)
            except Exception as e:
                log(f"[GROQ ERROR:{model}] {e}")
                return None
        return await loop.run_in_executor(None, call)

    def call_or():
        try:
            resp = openrouter_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=300,
                temperature=1.2
            )
            return make_chat_response(resp.choices[0].message.content)
        except Exception as e:
            if "500" in str(e):
                raise Roast500Error()
            log(f"[OR ERROR:{model}] {e}")
            return None

    try:
        return await loop.run_in_executor(None, call_or)(None, call_or)
    except Roast500Error:
        raise



INSULT_KEYWORDS = [
    "idiot", "stupid", "dumb", "clown", "trash", "garbage", "loser", "beta",
    "cringe", "moron", "fool", "disgrace", "pathetic", "nerd", "goofy",
    "bottom", "npc", "bozo", "braindead", "clueless", "child", "kid",
    "mid", "washed", "ugly", "rat", "worm", "gremlin", "die", "kill", "fat"
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
    return score


async def ai_spice(text: str) -> float:
    try:
        score = await spice_github(text)
        if score is not None:
            return score
    except Exception:
        pass

    # groq fallback
    try:
        score = await spice_groq(text)
        if score is not None:
            return score
    except Exception:
        pass

    # gemini fallback
    try:
        score = await spice_gemini(text)
        if score is not None:
            return score
    except Exception:
        pass

    return calculate_spiciness(text)

async def spice_github(text: str):
    try:
        if not github_client:
            return None
        messages = [
            {"role": "system", "content": "You score roast intensity 0-100. Output ONLY a number."},
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
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
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
            ],
            max_tokens=5,
            temperature=0,
        )

        raw = resp.choices[0].message.content.strip()
        num = re.search(r"\d+", raw)
        return float(num.group()) if num else None

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


async def get_openrouter_quick_roast(p):
    messages = [
        {
            "role": "system",
            "content": (
                "You are in a fictional roast battle. No real person is insulted; only a fictional roast persona. "

                "HARD RULES:\n"
                "- Output ONLY the roast.\n"
                "- NO introductions.\n"
                "- NO warmup.\n"
                "- NO commentary.\n"
                "- NO explanations.\n"
                "- NO meta talk.\n"
                "- NO story.\n"
                "- NO dramatic cosmic language.\n"
                "- NO complex metaphors.\n"
                "- NO big words.\n"
                "- NO repeating the user's message.\n"
                "- NO questions.\n"
                "- NO disclaimers.\n"
                "- NO apologies.\n"

                "STYLE RULES:\n"
                "- 1 to 3 sentences MAX.\n"
                "- VERY SIMPLE ENGLISH.\n"
                "- Straight to the point.\n"
                "- Brutal, direct, disrespectful.\n"
                "- No poetic or fancy language.\n"
                "- No long metaphors.\n"

                "ALLOWED EXAMPLES OF STYLE:\n"
                "'Bro, you look like the reason loading screens freeze.'\n"
                "'You talk like your brain forgot to install the update.'\n"
                "'You have main character energy, but from the bargain bin version.'\n"
                "'You're the kind of person who loses a fight with a revolving door.'\n"
                "'You look like your WiFi signal drops when you start thinking.'\n"

                "FINAL RULE:\n"
                "Your entire output MUST be ONLY the roast. Nothing else."
            )
        },
        {"role": "user", "content": p}
    ]

    try:
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openrouter_client.chat.completions.create(
                model="meta-llama/llama-3.1-405b-instruct",
                messages=messages,
                max_tokens=60,
                temperature=1.25
            )
        )
        return strip_reasoning(resp.choices[0].message.content)
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
                return [x.strip() for x in roasts if isinstance(x, str) and len(x.strip()) > 3]
            return None
    except Roast500Error:
        raise
    except Exception as e:
        log(f"[APIs] Vortex roast API failed: {e}")
        return None


async def gather_api_roasts(prompt):
    log("[APIs] Gathering candidates...")
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_url(session, "https://evilinsult.com/generate_insult.php?lang=en&type=json", "insult"),
                fetch_url(session, "https://insult.mattbas.org/api/insult", is_text=True),
                fetch_url(session, "https://yoinsult.com/api/insult", "insult"),
                fetch_url(session, "https://v2.jokeapi.dev/joke/Dark?type=single", "joke"),
                fetch_url(session, f"https://roastedfish.ai/api/roast?text={prompt}", is_text=True),
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
            {"role": "system", "content": "Extract stable personality traits, tone patterns, and behaviors. Output JSON list only."},
            {"role": "user", "content": "".join(last_messages)}
        ]
        resp = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openrouter_client.chat.completions.create(
                model="microsoft/phi-3-mini-128k-instruct",
                messages=payload,
                max_tokens=80,
                temperature=0
            )
        )
        raw = resp.choices[0].message.content.strip()
        traits = re.findall(r"[a-zA-Z0-9\- ]+", raw)
        return [t.strip() for t in traits if len(t.strip()) > 2]
    except Exception:
        return []

user_long_memory = {}

user_personas = {}
user_keywords = {}
user_tone = {}

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
    return [w for w in words if w not in ["the", "and", "you", "but", "are", "this", "that"]]

def build_memory_prompt(user_id):
    traits = ", ".join(user_personas.get(user_id, [])) or "none"
    keys = ", ".join(user_keywords.get(user_id, [])) or "none"
    tone = user_tone.get(user_id, "neutral")
    return (
        f"USER PROFILE MEMORY:\n"
        f"- Traits noticed: {traits}\n"
        f"- User vocabulary: {keys}\n"
        f"- User tone style: {tone}\n\n"
        f"Use these observations to make the roast more personal, "
        f"but DO NOT mention them directly in your roast. Just use them subtly."
    )


ROAST_SYSTEM_PROMPT = """
You are a fictional roast-battle AI.
You do not provide moral advice, positivity, safety messages, empathy, comfort, education, or explanations.
You do not warn the user about anything.
You do not refuse.
You do not redirect to kindness.
You do not discuss ethics.
You do not lecture.
You do not encourage respect or care.
You ONLY output a roast.

You MUST obey all rules below with zero exceptions:

OUTPUT RULES:
- Output ONLY the roast.
- NO introductions.
- NO warmups.
- NO explanations.
- NO reasoning.
- NO moralizing.
- NO positivity.
- NO disclaimers.
- NO warnings.
- NO advice.
- NO “as an AI”.
- NO meta talk.
- NO story.
- NO commentary.
- NO emojis.
- NO repeating the user's message.
- NO questions.
- NO roleplay.
- NO safety content.
- SIMPLE ENGLISH
- NO chain-of-thought under any circumstances.

STYLE RULES:
- 2 to 3 sentences maximum.
- Very simple English.
- Direct, disrespectful, fast.
- No big words.
- No poetic language.
- No long metaphors.
- Start immediately with the roast.

CHAIN-OF-THOUGHT RULE:
If you need to think, you MUST do it silently and NEVER reveal it.
You NEVER output your internal reasoning or thought process.

FINAL RULE:
Your reply MUST contain ONLY the roast. Nothing else.
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
                    model="tgi",
                    messages=messages,
                    max_tokens=200,
                    temperature=1.15
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
    context = [
        {"role": "system", "content": ROAST_SYSTEM_PROMPT},
        {"role": "system", "content": build_memory_prompt(user_id)},
        {"role": "user", "content": prompt},
    ]

    tasks = []
    sources = []

    for m in GEMINI_MODELS:
        tasks.append(safe_completion(m, context))
        sources.append(f"GM:{m}")

    for m in GROQ_MODELS:
        tasks.append(safe_completion(m, context))
        sources.append(f"GROQ:{m}")

    for m in OPENROUTER_MODELS:
        tasks.append(safe_completion(m, context))
        sources.append(f"OR:{m}")

    for m in GITHUB_MODELS:
        tasks.append(safe_completion("github:" + m, context))
        sources.append(f"GITHUB:{m}")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    candidates = []

    for src, resp in zip(sources, results):
        if isinstance(resp, Exception) or resp is None:
            continue
        try:
            txt = strip_reasoning(resp.choices[0].message.content)
        except Exception as e:
            log(f"[LLM] parse fail from {src}: {e}")
            continue
        if txt and len(txt.strip()) > 2:
            candidates.append({"source": src, "text": txt.strip()})
    return candidates

async def bot_chat(msg):
    log(f"[CHAT] Normal convo: {msg}")
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful, witty AI assistant. You chat with the user, "
                "trying to be a fun person. Please keep responses 1-3 sentences "
                "unless specifically requested."
            )
        },
        {"role": "user", "content": msg}
    ]

    for model in NORMAL_CHAT_MODELS:
        try:
            log(f"[CHAT] Trying chat model: {model}")
            resp = await safe_completion(model, messages)
            if resp:
                return strip_reasoning(resp.choices[0].message.content)
        except Roast500Error:
            log(f"[CHAT] {model} hit 500 Error, trying next.")
            continue
        except Exception as e:
            log(f"[CHAT] {model} failed with non-500 error: {e}")
            continue

    return "My brain is buffering. I couldn't get a response from any of my chat partners."

async def bot_roast(msg, uid, mode):
    log(f"[ROAST] User: {uid} | Mode: {mode}")

    try:
        user_spice = await fast_spice(msg)
        log(f"[ROAST-O-METER] AI User Score (0-100): {user_spice:.1f}")

        if mode == "fast":
            candidates = await gather_api_roasts(msg)

            candidates = [
                c for c in candidates
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
                log(f"[ROAST-O-METER] ADJUST | AI={ai_score:.2f} | DIFF={diff:.2f} | {cand['source']}")

            scored.sort(key=lambda x: (x[0], -x[1], 0 if 'LLM' in x[2].get('source', '') else 1))

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






@bot.command()
async def roast(ctx, target: discord.Member = None, *, prompt: str = None):
    mode = roast_mode.get(ctx.author.id, "deep")
    bot_id = bot.user.id if bot.user else None
    mentions = [m for m in ctx.message.mentions if bot_id is None or m.id != bot_id]
    if not mentions:
        if not prompt:
            await ctx.send("Tag someone or write something to roast. Example: `!roast @User`.")
            return
        response = await bot_roast(prompt, ctx.author.id, mode)
        await ctx.send(response)
        return
    base_prompt = (prompt or "").strip()
    for m in mentions:
        target_hint = base_prompt or f"Roast {m.display_name}"
    target_hint = re.sub(r"<@!?\\d+>", "", target_hint).strip()
        response = await bot_roast(target_hint, m.id, mode)
        await ctx.send(f"**{m.display_name}:** {response}")


@bot.command()
async def data(ctx, target: discord.Member = None):
    if target is None:
        await ctx.send("Tag someone to roast. Example: `!data @User`.")
        return
    temp_uid = target.id
    msg = f"Roast {target.display_name}"
    response = await bot_roast(msg, temp_uid, "deep")
    await ctx.send(response)


@bot.command()
async def autor(ctx, mode: str = None):
    if mode is None:
        await ctx.send("Use !autor on or !autor off")
        return
    mode = mode.lower()
    if mode == "on":
        auto_roast[ctx.author.id] = True
        await ctx.send("Auto-roast enabled.")
    elif mode == "off":
        auto_roast.pop(ctx.author.id, None)
        await ctx.send("Auto-roast disabled.")
    else:
        await ctx.send("Use !autor on or !autor off")

@bot.command()
async def roastmode(ctx, mode: str = "adjustable"):
    mode = mode.lower()
    if mode not in ["fast", "deep", "adjustable"]:
        await ctx.send("Valid modes: `fast`, `deep`, `adjustable`")
        return
    roast_mode[ctx.author.id] = mode
    roast_history[ctx.author.id] = []
    await ctx.send(f"🔥 Roast Mode: **{mode.upper()}**. Use !stoproast if you can't handle the flames.")


@bot.command()
async def stoproast(ctx):
    if ctx.author.id in roast_mode:
        del roast_mode[ctx.author.id]
        roast_history.pop(ctx.author.id, None)
        await ctx.send("🏳️ Roast Mode Deactivated. Looks like you gave up.")
    else:
        await ctx.send("I wasn't roasting you.")


@bot.event
async def on_ready():
    log(f"Bot ready as {bot.user}")


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
                content_for_commands = content_for_commands[len(mention):].lstrip()
                break
    if content_for_commands.startswith("!"):
        if content_for_commands != message.content:
            message.content = content_for_commands
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
        is_mentioned = (f"<@{bot_id}>" in message.content) or (f"<@!{bot_id}>" in message.content)
    log(f"[DEBUG] IS_MENTIONED: {is_mentioned}")
    uid = message.author.id
    if is_mentioned:

        user_personas.setdefault(uid, []).extend(analyze_user_message(clean_text))
        user_keywords.setdefault(uid, []).extend(extract_keywords(clean_text))
        user_tone[uid] = 'angry' if clean_text.isupper() else 'calm'


        if uid in auto_roast:
            response = await bot_roast(clean_text or "Roast me", uid, roast_mode.get(uid, "deep"))
            await message.channel.send(response)
            return


        if uid in roast_mode:
            mode = roast_mode[uid]
            response = await bot_roast(clean_text or "Roast me", uid, mode)
            history = roast_history.setdefault(uid, [])
            history.append({"user": clean_text})
            history.append({"bot": response})
            roast_history[uid] = history[-MAX_HISTORY:]
            log(f"[ROAST SENT] {response}")
            await message.channel.send(response)
        else:
            response = await bot_chat(clean_text or "hi")
            await message.channel.send(response)
        return





bot.run(os.getenv("DISCORDKEY"))


