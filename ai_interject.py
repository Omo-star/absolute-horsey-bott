import re
from typing import List

MAX_WORDS = 10
MAX_CHARS = 80

INTERJECT_MODELS: List[str] = [
    "groq:llama-3.1-8b-instant",
    "github:gpt-4o-mini",
    "gemini-2.0-flash",
    "openai:gpt-4o-mini",
]

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
        try:
            resp = await safe_completion(model, messages)
            if not resp:
                continue

            text = extract_text_with_logging(f"INTERJECT:{model}", resp)
            if not text:
                continue

            text = text.strip()
            text = re.sub(r"\s+", " ", text)
            text = text.split("\n")[0]
            text = text[:MAX_CHARS]

            words = text.split()
            if len(words) > MAX_WORDS:
                text = " ".join(words[:MAX_WORDS])

            text = text.strip()

            if len(text) >= 2:
                return text

        except Exception:
            continue

    return ""
