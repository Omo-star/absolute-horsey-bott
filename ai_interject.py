import re
import asyncio
from bbot import safe_completion
from bbot import extract_text_with_logging
from typing import Optional

MAX_WORDS = 10
MAX_CHARS = 80

async def ai_interject_line(bucket: str, content: str) -> str:
    system = (
        "you are a real discord user reacting naturally\n"
        "write one short casual response\n"
        "1 to 10 words max\n"
        "no capitalization\n"
        "no emojis unless they fit naturally\n"
        "no explanations\n"
        "no analysis\n"
        "never sound formal\n"
        "if the message is a greeting respond with a greeting\n"
        "if the message is a question respond with curiosity or confusion\n"
        "if the message is emotional respond with empathy\n"
        "output only the message\n"
    )

    user = (
        f"message type: {bucket}\n"
        f"message content: \"{content}\"\n\n"
        "reply naturally like a human would in chat"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

    try:
        resp = await safe_completion("gemini-2.0-flash", messages)
        if not resp:
            return ""
        text = extract_text_with_logging("INTERJECT_AI", resp)
        if not text:
            return ""
    except Exception:
        return ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.split("\n")[0]
    text = text[:MAX_CHARS]

    words = text.split()
    if len(words) > MAX_WORDS:
        text = " ".join(words[:MAX_WORDS])

    text = text.strip(" .,!?:;")

    if len(text) < 2:
        return ""

    return text
