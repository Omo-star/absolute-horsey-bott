import re

FUSBOT_ALIASES = {
    "fusbot",
    "fus bot",
    "@fusbot",
    "fus-bot",
    "fus_bot",
    "fusboi",
    "fusb0t",
    "fus-b0t",
    "FUSBOT",
    "FuSBot",
}

_ALIAS_PATTERNS = [
    re.compile(rf"\b{re.escape(a)}\b", re.IGNORECASE)
    for a in FUSBOT_ALIASES
]

def mentions_fusbot(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _ALIAS_PATTERNS)
