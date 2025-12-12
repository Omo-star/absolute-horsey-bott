import random
import time
import asyncio
import re
import math
from collections import defaultdict, deque, Counter

import discord


IGNORE_PREFIXES = ("!", "/", ".")

BASE_REACT_PROB_MENTIONED = 0.38
BASE_REACT_PROB_PASSIVE = 0.12

HARD_MIN_GAP_CHANNEL = 10.0
HARD_MIN_GAP_USER = 14.0

SOFT_COOLDOWN_CHANNEL = 22.0
SOFT_COOLDOWN_USER = 30.0

MAX_P_LEN_BONUS = 0.22
LEN_BONUS_DENOM = 260.0

MAX_FAMILIARITY_BONUS = 0.10
FAMILIARITY_SCALE = 0.010

MAX_CHANNEL_AFFINITY_BONUS = 0.06
CHANNEL_AFFINITY_SCALE = 0.006

MAX_RECIPROCITY_BONUS = 0.08

FATIGUE_WINDOW_SEC = 220.0
FATIGUE_STEP = 0.042
MAX_FATIGUE_PENALTY = 0.30

SCROLL_PAST_CHANCE = 0.06
MOOD_DRIFT_CHANCE = 0.018

REGRET_CHANCE = 0.010
REGRET_DELAY_RANGE = (1.2, 5.0)

REACTION_DIVERSITY_WINDOW = 18
REACTION_REPEAT_PENALTY = 0.20

CULTURE_MEMORY_MAX = 240
CULTURE_HALF_LIFE_SEC = 60 * 45

CONTEXT_WINDOW = 9
CONTEXT_ACTIVE_SEC = 55.0

READING_WPM = (185, 310)
READING_MIN = 0.18
READING_MAX = 2.0

TYPE_BASE = (0.35, 1.05)
TYPE_PER_CHAR = (0.010, 0.022)
TYPE_MAX = 5.8
TYPE_HESITATION_CHANCE = 0.22
TYPE_HESITATION_RANGE = (0.18, 0.75)

LOW_EFFORT = {
    "hi", "hey", "hello", "yo", "sup", "ok", "okay", "k", "kk", "lol", "lmao", "nah", "bruh", "yup", "nope", "bet"
}

FUNNY_KEYS = [
    "lol","lmao","lmfao","rofl","😂","😭","💀","🤣","😭😭","😂😂","💀💀",
    "dead","im dead","i'm dead","im crying","i'm crying","crying",
    "im weak","i'm weak","im losing it","i’m losing it",
    "im screaming","i'm screaming","screaming",
    "help","HELP","pls","please","nahhh","nahh","nahhhhh",
    "bro","bruh","bro 😭","bro 💀","bro 😂",
    "wtf","what the hell","what is this","why is this funny",
    "this killed me","this is killing me","this shouldnt be funny",
    "this shouldn’t be funny","i cant","i can’t","cant stop laughing",
    "im wheezing","i'm wheezing","wheezing",
    "im done","i'm done","im gone","i'm gone",
    "who let him cook","who let her cook",
    "why did this work","how is this funny",
    "nah this crazy","nah this wild","this is insane 😭",
    "i’m actually crying","im actually crying"
]

HYPE_KEYS = [
    "lets go","let's go","lfg","LFG","fire","so fire","this fire",
    "goat","the goat","crazy","insane","actually insane",
    "holy","holy shit","holy crap",
    "W","big W","huge W","massive",
    "clean","smooth","perfect","elite","top tier",
    "cook","cooked","he cooked","she cooked","they cooked",
    "let him cook","let her cook","nah he cooked",
    "this goes hard","this hard","hard af","hard asf",
    "this slaps","goes insane","this insane",
    "no shot","cant believe this","how is this real",
    "this is fire","this heat","this gas",
    "so good","so clean","played perfectly",
    "nah this different","this different","built different"
]

SAD_KEYS = [
    "sad","im sad","i'm sad","lowkey sad","kinda sad",
    "tired","im tired","i'm tired","so tired",
    "exhausted","burnt out","drained",
    "upset","cry","crying","tearing up",
    "depressed","pain","lonely","alone",
    "anxious","stressed","overwhelmed",
    "miserable","im miserable","i'm miserable",
    "this sucks","everything sucks","life sucks",
    "im done","i'm done","cant do this","i can’t do this",
    "im exhausted","i'm exhausted",
    "rough day","bad day","long day",
    "im not okay","i'm not okay","not okay",
    "just tired","just tired of everything"
]

ACK_KEYS = [
    "thanks","thx","ty","thank you","appreciate","appreciate it",
    "got it","gotcha","ok","okay","ok cool","cool",
    "sounds good","makes sense","fair","bet","noted",
    "all good","alright","for sure","fs",
    "yea","yeah","yep","yup","mm","mhm",
    "i see","see","copy","copy that", "k", "kk"
]

AGREE_KEYS = [
    "true","facts","real","fr", "frfr", "same","exactly","100%",
    "yep","yup","yeah","so real","real af",
    "literally","on god","ong",
    "thats right","that's right",
    "you right","u right","correct",
    "absolutely","definitely",
    "couldnt agree more","couldn’t agree more",
    "this","this exactly","that part"
]

DISBELIEF_KEYS = [
    "no way","no shot","cap","bs","bull","bullshit",
    "fake","sure buddy","nah","nahh","nahhh",
    "aint no","ain't no","be fr","be serious",
    "you lying","ur lying","you’re lying",
    "theres no way","there's no way",
    "calling cap","stop the cap",
    "not a chance","no chance",
    "im not buying this","i'm not buying this",
    "this fake","yeah right"
]

QUESTION_KEYS = [
    "?","??","???",
    "why","how","what","when","where","who","which",
    "why is","how does","what is","what are",
    "anyone know","does anyone","can someone",
    "wtf is","what the hell is",
    "how did","why did",
    "is this","are we","did this",
    "am i","should i","can i",
    "wait what","hold up what","huh"
]

DEFAULT_BUCKETS = {
    "ack": ["👍","👌","✅","☑️"],
    "see": ["👀","👁️","🫣"],
    "funny": ["😂","😭","💀","🤣","😹"],
    "hype": ["🔥","💯","🚀","🙌","✨"],
    "sad": ["😔","🫂","❤️","😞","🥲"],
    "question": ["❓","🤔","🧐"],
    "agree": ["✅","💯","🤝","👍"],
    "disbelief": ["🧢","😳","🤨","😐"]
}


_last_channel_time = {}
_last_user_time = {}
_recent_reacts = deque()
_recent_emojis = deque(maxlen=REACTION_DIVERSITY_WINDOW)

_channel_msgs = defaultdict(lambda: deque(maxlen=CONTEXT_WINDOW))
_channel_culture = defaultdict(lambda: deque(maxlen=CULTURE_MEMORY_MAX))
_channel_emoji_counts = defaultdict(Counter)

_user_familiarity = defaultdict(int)
_user_channel_affinity = defaultdict(int)
_user_recent_emoji = defaultdict(lambda: deque(maxlen=8))
_user_emoji_pref = defaultdict(Counter)
_user_received_reacts = defaultdict(int)
_user_given_reacts = defaultdict(int)

_moods = ["neutral", "warm", "tired", "silly", "focused"]
_current_mood = random.choice(_moods)

_word_re = re.compile(r"\w+")
_space_re = re.compile(r"\s+")


def _now():
    return time.time()


def _norm(text: str) -> str:
    return _space_re.sub(" ", text.lower().strip())


def _words(text: str):
    return _word_re.findall(text.lower())


def _low_effort(text: str) -> bool:
    t = _norm(text)
    if not t:
        return True
    if len(t) <= 4:
        return True
    return t in LOW_EFFORT


def _has_any(text: str, keys) -> bool:
    t = text.lower()
    return any(k in t for k in keys)


def _is_question(content: str) -> bool:
    t = content.lower()
    if "?" in content and len(content) > 8:
        return True
    if len(t) < 7:
        return False
    return any(t.startswith(k + " ") for k in ("why", "how", "what", "when", "where", "who", "which"))


def _cooldown(channel_id: int, user_id: int) -> bool:
    t = _now()
    if t - _last_channel_time.get(channel_id, 0.0) < HARD_MIN_GAP_CHANNEL:
        return True
    if t - _last_user_time.get(user_id, 0.0) < HARD_MIN_GAP_USER:
        return True
    return False


def _mark(channel_id: int, user_id: int, emoji: str):
    t = _now()
    _last_channel_time[channel_id] = t
    _last_user_time[user_id] = t
    _recent_reacts.append(t)
    _recent_emojis.append(emoji)
    _user_recent_emoji[user_id].append(emoji)
    _user_familiarity[user_id] += 1
    _user_channel_affinity[(user_id, channel_id)] += 1


def _fatigue_penalty() -> float:
    cutoff = _now() - FATIGUE_WINDOW_SEC
    while _recent_reacts and _recent_reacts[0] < cutoff:
        _recent_reacts.popleft()
    return min(len(_recent_reacts) * FATIGUE_STEP, MAX_FATIGUE_PENALTY)


def _circadian_penalty() -> float:
    lt = time.localtime()
    hour = lt.tm_hour
    wday = lt.tm_wday
    if 2 <= hour <= 6:
        return 0.12
    if hour >= 0 and hour <= 1:
        return 0.07
    if wday >= 5 and hour >= 23:
        return 0.06
    return 0.0


def _soft_cooldown_penalty(channel_id: int, user_id: int) -> float:
    t = _now()
    dc = t - _last_channel_time.get(channel_id, 0.0)
    du = t - _last_user_time.get(user_id, 0.0)
    pc = 0.0 if dc >= SOFT_COOLDOWN_CHANNEL else (1.0 - dc / SOFT_COOLDOWN_CHANNEL) * 0.18
    pu = 0.0 if du >= SOFT_COOLDOWN_USER else (1.0 - du / SOFT_COOLDOWN_USER) * 0.22
    return pc + pu


def _diversity_penalty(emoji: str) -> float:
    if not _recent_emojis:
        return 0.0
    repeats = sum(1 for e in _recent_emojis if e == emoji)
    if repeats <= 0:
        return 0.0
    return min(repeats * (REACTION_REPEAT_PENALTY / 2.0), REACTION_REPEAT_PENALTY)


def _maybe_shift_mood():
    global _current_mood
    if random.random() < MOOD_DRIFT_CHANCE:
        _current_mood = random.choice(_moods)


def _context_activity(channel_id: int) -> float:
    q = _channel_msgs[channel_id]
    if len(q) < 2:
        return 0.0
    t = _now()
    recent = [ts for ts, _ in q if t - ts <= CONTEXT_ACTIVE_SEC]
    if not recent:
        return 0.0
    density = min(len(recent) / 5.0, 1.0)
    return density


def _culture_top_emojis(channel_id: int, k: int = 6):
    counts = _channel_emoji_counts[channel_id]
    if not counts:
        return []
    return [e for e, _ in counts.most_common(k)]


def _culture_decay(channel_id: int):
    t = _now()
    dq = _channel_culture[channel_id]
    while dq:
        ts, emoji = dq[0]
        if t - ts <= CULTURE_HALF_LIFE_SEC:
            break
        dq.popleft()
        if _channel_emoji_counts[channel_id][emoji] > 0:
            _channel_emoji_counts[channel_id][emoji] -= 1
            if _channel_emoji_counts[channel_id][emoji] <= 0:
                del _channel_emoji_counts[channel_id][emoji]


def observe_reaction(channel_id: int, user_id: int, emoji: str):
    if not emoji:
        return
    _culture_decay(channel_id)
    t = _now()
    _channel_culture[channel_id].append((t, emoji))
    _channel_emoji_counts[channel_id][emoji] += 1
    _user_emoji_pref[user_id][emoji] += 1
    _user_given_reacts[user_id] += 1


def observe_received_reaction(user_id: int):
    _user_received_reacts[user_id] += 1


def _reciprocity_bonus(user_id: int) -> float:
    given = _user_given_reacts.get(user_id, 0)
    received = _user_received_reacts.get(user_id, 0)
    if given <= 0:
        return 0.0
    ratio = min(received / max(given, 1), 2.0)
    return min((ratio - 0.4) * 0.06, MAX_RECIPROCITY_BONUS) if ratio > 0.4 else 0.0


def _pick_bucket(text: str, content: str) -> str:
    t = text.lower()
    if _is_question(content):
        return "question"
    if _has_any(t, SAD_KEYS):
        return "sad"
    if _has_any(t, FUNNY_KEYS):
        return "funny"
    if _has_any(t, HYPE_KEYS):
        return "hype"
    if _has_any(t, ACK_KEYS):
        return "ack"
    if _has_any(t, AGREE_KEYS):
        return "agree"
    if _has_any(t, DISBELIEF_KEYS):
        return "disbelief"
    if len(content) > 90:
        return "see"
    return "ack"


def _candidate_emojis(channel_id: int, user_id: int, bucket: str):
    base = list(DEFAULT_BUCKETS.get(bucket, DEFAULT_BUCKETS["ack"]))
    _culture_decay(channel_id)
    culture = _culture_top_emojis(channel_id, k=8)
    prefs = [e for e, _ in _user_emoji_pref[user_id].most_common(5)]
    pool = []
    pool.extend(base)
    pool.extend(culture)
    pool.extend(prefs)
    seen = set()
    uniq = []
    for e in pool:
        if e and e not in seen:
            seen.add(e)
            uniq.append(e)
    return uniq[:14] if uniq else base


def _mood_tweak(bucket: str):
    if _current_mood == "tired":
        if bucket in ("funny", "hype"):
            return "see"
        if bucket == "question":
            return "question"
        return "see"
    if _current_mood == "warm":
        if bucket == "sad":
            return "sad"
        if bucket in ("ack", "agree"):
            return "agree"
        return bucket
    if _current_mood == "silly":
        if bucket in ("ack", "agree", "disbelief"):
            return "funny"
        return bucket
    if _current_mood == "focused":
        if bucket in ("funny", "hype"):
            return "ack"
        return bucket
    return bucket


def _choose_emoji(channel_id: int, user_id: int, bucket: str):
    bucket = _mood_tweak(bucket)
    candidates = _candidate_emojis(channel_id, user_id, bucket)
    weights = []
    for e in candidates:
        w = 1.0
        w += min(_user_emoji_pref[user_id].get(e, 0) * 0.06, 0.55)
        w += min(_channel_emoji_counts[channel_id].get(e, 0) * 0.025, 0.65)
        w -= _diversity_penalty(e)
        if e in _user_recent_emoji[user_id]:
            w *= 0.55
        if e in _recent_emojis:
            w *= 0.78
        weights.append(max(w, 0.08))
    total = sum(weights)
    r = random.random() * total
    acc = 0.0
    for e, w in zip(candidates, weights):
        acc += w
        if r <= acc:
            return e
    return random.choice(candidates)


def _p_react(message: discord.Message, mentioned: bool) -> float:
    content = message.content.strip()
    L = len(content)
    p = BASE_REACT_PROB_MENTIONED if mentioned else BASE_REACT_PROB_PASSIVE
    p += min(L / LEN_BONUS_DENOM, MAX_P_LEN_BONUS)
    p += min(_user_familiarity[message.author.id] * FAMILIARITY_SCALE, MAX_FAMILIARITY_BONUS)
    p += min(_user_channel_affinity[(message.author.id, message.channel.id)] * CHANNEL_AFFINITY_SCALE, MAX_CHANNEL_AFFINITY_BONUS)
    p += _reciprocity_bonus(message.author.id)
    p += _context_activity(message.channel.id) * 0.06
    p -= _fatigue_penalty()
    p -= _circadian_penalty()
    p -= _soft_cooldown_penalty(message.channel.id, message.author.id)

    if any(ch in content for ch in ("http://", "https://")) and L < 40:
        p -= 0.08

    if L > 6 and content.isupper():
        p += 0.04

    if message.mentions and not mentioned:
        p += 0.03

    p = max(min(p, 0.88), 0.0)
    return p


def _should_scroll_past(channel_id: int) -> bool:
    a = _context_activity(channel_id)
    miss = SCROLL_PAST_CHANCE + a * 0.03
    if _current_mood == "tired":
        miss += 0.05
    return random.random() < miss


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

    _maybe_shift_mood()

    if _should_scroll_past(message.channel.id):
        return

    p = _p_react(message, mentioned)

    if random.random() > p:
        return

    text = content.lower()
    bucket = _pick_bucket(text, content)
    emoji = _choose_emoji(message.channel.id, message.author.id, bucket)

    try:
        await message.add_reaction(emoji)
        _mark(message.channel.id, message.author.id, emoji)
        if random.random() < REGRET_CHANCE:
            await asyncio.sleep(random.uniform(*REGRET_DELAY_RANGE))
            try:
                await message.remove_reaction(emoji, message.guild.me)
            except:
                pass
    except:
        return

async def human_delay(channel: discord.abc.Messageable, reply_text: str = ""):
    txt = reply_text or ""
    w = max(len(_words(txt)), 1)
    wpm = random.uniform(*READING_WPM)
    read_time = min(max((w / wpm) * 60.0, READING_MIN), READING_MAX)

    base = random.uniform(*TYPE_BASE)
    per = random.uniform(*TYPE_PER_CHAR)
    type_time = base + min(len(txt) * per, TYPE_MAX)

    total = read_time + type_time
    chunks = max(1, int(total / random.uniform(1.15, 1.9)))
    remaining = total

    for _ in range(chunks):
        d = min(remaining, random.uniform(0.55, 1.45))
        remaining -= d
        try:
            async with channel.typing():
                await asyncio.sleep(d)
        except:
            await asyncio.sleep(d)

        if random.random() < TYPE_HESITATION_CHANCE:
            await asyncio.sleep(random.uniform(*TYPE_HESITATION_RANGE))


def observe_channel_message(channel_id: int, content: str):
    if not content:
        return
    _channel_msgs[channel_id].append((_now(), content))

_last_speak_time = {}
_last_speak_confidence = defaultdict(lambda: 0.5)
_last_channel_embarrassment = defaultdict(float)

SPEAK_COOLDOWN = 75.0
EMBARRASSMENT_HALF_LIFE = 180.0

BASE_INTERRUPT_PROB = 0.012
MAX_INTERRUPT_PROB = 0.26

def _decay_embarrassment(channel_id: int):
    t = _now()
    last = _last_speak_time.get(channel_id)
    if not last:
        return
    age = t - last
    if age <= 0:
        return
    decay = math.exp(-age / EMBARRASSMENT_HALF_LIFE)
    _last_channel_embarrassment[channel_id] *= decay

def _conversation_pressure(channel_id: int) -> float:
    q = _channel_msgs[channel_id]
    if len(q) < 3:
        return 0.0
    t = _now()
    recent = [(ts, msg) for ts, msg in q if t - ts < 45.0]
    if len(recent) < 3:
        return 0.0
    lengths = [len(m) for _, m in recent]
    avg_len = sum(lengths) / len(lengths)
    density = min(len(recent) / 6.0, 1.0)
    emotional = sum(
        1 for _, m in recent
        if any(x in m.lower() for x in ("??", "wtf", "bro", "nah", "crazy"))
    ) * 0.08
    return min(density * 0.28 + min(avg_len / 150.0, 0.18) + emotional, 0.62)

def _unanswered_question_pressure(channel_id: int) -> float:
    q = _channel_msgs[channel_id]
    if not q:
        return 0.0
    ts, msg = q[-1]
    if not _is_question(msg):
        return 0.0
    age = _now() - ts
    if age < 4.0 or age > 32.0:
        return 0.0
    return min((age - 4.0) / 28.0, 1.0) * 0.48

def _relevance_pressure(message: discord.Message) -> float:
    uid = message.author.id
    score = 0.0
    score += min(_user_channel_affinity[(uid, message.channel.id)] * 0.022, 0.14)
    score += min(_user_familiarity[uid] * 0.017, 0.12)
    return score

def _confidence_decay(channel_id: int) -> float:
    base = _last_speak_confidence[channel_id]
    decay = 1.0 - min(_last_channel_embarrassment[channel_id], 0.85)
    return max(base * decay, 0.25)

def should_interject(message: discord.Message) -> float:
    if not message.guild:
        return 0.0
    if message.author.bot:
        return 0.0

    channel_id = message.channel.id
    now = _now()

    last = _last_speak_time.get(channel_id, 0.0)
    if now - last < SPEAK_COOLDOWN:
        return 0.0

    _decay_embarrassment(channel_id)

    pressure = 0.0
    pressure += _conversation_pressure(channel_id)
    pressure += _unanswered_question_pressure(channel_id)
    pressure += _relevance_pressure(message)

    if _current_mood == "tired":
        pressure *= 0.6
    elif _current_mood == "silly":
        pressure *= 1.18
    elif _current_mood == "focused":
        pressure *= 0.85

    pressure -= _fatigue_penalty()
    pressure -= _circadian_penalty()
    pressure -= _last_channel_embarrassment[channel_id] * 0.55

    confidence = _confidence_decay(channel_id)

    p = BASE_INTERRUPT_PROB + pressure * confidence
    p = max(min(p, MAX_INTERRUPT_PROB), 0.0)

    if random.random() < p:
        _last_speak_time[channel_id] = now
        _last_speak_confidence[channel_id] = confidence * random.uniform(0.88, 0.97)
        _last_channel_embarrassment[channel_id] += random.uniform(0.12, 0.28)
        return p

    return 0.0

