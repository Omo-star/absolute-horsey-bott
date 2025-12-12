import re
import time
from typing import List
import asyncio
import re
import os
import google.generativeai as genai
from groq import Groq
from openai import OpenAI

groq_client = Groq(api_key=os.getenv("GROQ"))
openrouter_client = OpenAI(
    api_key=os.getenv("OPENROUTER_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

def extract_text_with_logging(model_name, resp):
    try:
        c = resp.choices[0]
        if hasattr(c, "message") and hasattr(c.message, "content"):
            return c.message.content or ""
    except:
        pass
    return ""

def strip_reasoning(text):
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<reasoning>.*?</reasoning>", "", text, flags=re.DOTALL)
    return text.strip()
async def safe_completion(model: str, messages):
    loop = asyncio.get_event_loop()

    def wrap(text):
        class Msg: pass
        class Ch: pass
        class Resp: pass
        m = Msg()
        c = Ch()
        r = Resp()
        m.content = text
        c.message = m
        r.choices = [c]
        return r

    if model.startswith("groq:"):
        actual = model.split(":", 1)[1]
        def call():
            resp = groq_client.chat.completions.create(
                model=actual,
                messages=messages,
                max_tokens=40,
                temperature=1.0,
            )
            return wrap(resp.choices[0].message.content)
        return await loop.run_in_executor(None, call)

    if model.startswith("github:") and github_client:
        actual = model.split(":", 1)[1]
        def call():
            resp = github_client.chat.completions.create(
                model=actual,
                messages=messages,
                max_tokens=40,
                temperature=1.0,
            )
            return wrap(resp.choices[0].message.content)
        return await loop.run_in_executor(None, call)

    if model.startswith("gemini"):
        def call():
            user_text = "\n".join(
                m["content"] for m in messages if m["role"] == "user"
            )
            resp = genai.GenerativeModel(model).generate_content(user_text)
            return wrap(resp.text if hasattr(resp, "text") else "")
        return await loop.run_in_executor(None, call)
    def call():
        resp = openrouter_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=40,
            temperature=1.0,
        )
        return wrap(resp.choices[0].message.content)

    return await loop.run_in_executor(None, call)


MAX_WORDS = 10
MAX_CHARS = 80
DEBUG = True

def hlog(*x):
    if not DEBUG:
        return
    ts = time.strftime("%H:%M:%S", time.localtime())
    print(f"[AI_INTERJECT {ts}]", *x)

INTERJECT_MODELS: List[str] = [
    "groq:llama-3.1-8b-instant",
    "github:gpt-4o-mini",
    "gemini-2.0-flash",
    "openai:gpt-4o-mini",
]

async def ai_interject_line(bucket: str, content: str) -> str:
    hlog("AI_INTERJECT start bucket=", bucket, "content=", repr(content))

    system = (
        "you are a real discord user reacting naturally\n"
        "write one short casual response\n"
        "1 to 10 words max\n"
        "no capitalization\n"
        "no emojis unless they fit naturally\n"
        "no explanations\n"
        "no analysis\n"
        "never sound formal\n"
        "use slang too\n"
        "if the message is a greeting respond with a greeting\n"
        "if the message is a question respond with curiosity or confusion\n"
        "if the message is emotional respond with empathy\n"
        "output only the message\n"
    )

    user = (
        f"message type: {bucket}\n"
        f"message content: \"{content}\""
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    for model in INTERJECT_MODELS:
        hlog("AI_INTERJECT trying model:", model)

        try:
            resp = await safe_completion(model, messages)

            if not resp:
                hlog("AI_INTERJECT model", model, "returned no resp")
                continue

            text = extract_text_with_logging(f"INTERJECT:{model}", resp)

            if not text:
                hlog("AI_INTERJECT model", model, "returned empty text")
                continue

            raw = text
            text = text.strip()
            text = re.sub(r"\s+", " ", text)
            text = text.split("\n")[0]
            text = text[:MAX_CHARS]

            words = text.split()
            if len(words) > MAX_WORDS:
                hlog("AI_INTERJECT model", model, "too many words:", len(words))
                text = " ".join(words[:MAX_WORDS])

            text = text.strip()

            if len(text) < 2:
                hlog(
                    "AI_INTERJECT model",
                    model,
                    "rejected after cleanup, raw=",
                    repr(raw),
                )
                continue

            hlog("AI_INTERJECT success model=", model, "text=", repr(text))
            return text

        except Exception as e:
            hlog("AI_INTERJECT exception model=", model, "err=", e)
            continue

    hlog("AI_INTERJECT failed all models, returning empty")
    return ""
