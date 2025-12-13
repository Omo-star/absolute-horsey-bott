import asyncio
import time
import random
import math
import json
import os
import re
from mentions import mentions_fusbot
from ai_interject import ai_interject_line
from collections import defaultdict, deque, Counter
from typing import Any, Awaitable, Dict, Deque, List, Tuple, Optional, Callable
import discord

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  
    "\U0001F600-\U0001F64F"  
    "\U0001F680-\U0001F6FF"  
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"        
    "\u2700-\u27BF"
    "]",
    flags=re.UNICODE,
)


DEBUG = True

def hlog(*x: Any) -> None:
    if not DEBUG:
        return
    ts = time.strftime("%H:%M:%S", time.localtime())
    print(f"[BRAIN {ts}]", *x)

def _now() -> float:
    return time.time()

_word_re = re.compile(r"\w+")
_space_re = re.compile(r"\s+")

def _norm(t: str) -> str:
    return _space_re.sub(" ", (t or "").lower().strip())

def _words(t: str) -> List[str]:
    return _word_re.findall((t or "").lower())

IGNORE_PREFIXES = ("!", "/", ".")

STATE_LURKING = "lurking"
STATE_ENGAGED = "engaged"
STATE_LEADING = "leading"
STATE_WITHDRAWING = "withdrawing"

BASE_REACT_MENTION = 0.44
BASE_REACT_PASSIVE = 0.17

BASE_INTERRUPT_PROB = 0.085
MAX_INTERRUPT_PROB = 0.64

HARD_MIN_GAP_CHANNEL = 7.5
HARD_MIN_GAP_USER = 10.5

SOFT_COOLDOWN_CHANNEL = 18.0
SOFT_COOLDOWN_USER = 24.0

GUILD_EMOJI_HALF_LIFE = 24 * 3600 

FATIGUE_WINDOW_SEC = 240.0
FATIGUE_STEP = 0.045
MAX_FATIGUE_PENALTY = 0.34

CULTURE_MEMORY_MAX = 320
CULTURE_HALF_LIFE_SEC = 3200.0

CONTEXT_WINDOW = 14
CONTEXT_ACTIVE_SEC = 70.0

REACTION_DIVERSITY_WINDOW = 22
REACTION_REPEAT_PENALTY = 0.22

READING_WPM = (190, 330)
READING_MIN = 0.14
READING_MAX = 2.3

TYPE_BASE = (0.28, 1.0)
TYPE_PER_CHAR = (0.009, 0.025)
TYPE_MAX = 6.4
TYPE_HESITATION_CHANCE = 0.26
TYPE_HESITATION_RANGE = (0.14, 0.95)

REGRET_CHANCE = 0.012
REGRET_DELAY_RANGE = (1.0, 5.0)

SPEAK_COOLDOWN_BASE = 70.0
EMBARRASSMENT_HALF_LIFE = 195.0

SELF_REFLECT_EVERY = 240.0
PERSIST_EVERY = 180.0

MAX_CHANNEL_BOLDNESS = 1.35
MIN_CHANNEL_BOLDNESS = 0.55

LOW_EFFORT = {
    "hi","hey","hello","yo","sup","ok","okay","k","kk","lol","lmao","nah","bruh","yup","nope","bet",
    "true","facts","real","fr","frfr","same","exactly","100%","yep","yup","yeah","mm","mhm","aight",
    "word","sure","idk","i dunno","ight","👍","💀","😭","😂","🤣"
}

FUNNY_KEYS = [
    "lol","lmao","lmfao","rofl","😂","😭","💀","🤣","😹",
    "dead","im dead","i'm dead","im crying","i'm crying","crying","im weak","i'm weak","wheezing",
    "im losing it","i’m losing it","im screaming","i'm screaming","help","pls","please",
    "bro","bruh","wtf","what the hell","this killed me","this is killing me","this shouldnt be funny","i cant","i can’t",
    "im wheezing","i'm wheezing","im done","i'm done","im gone","i'm gone","who let him cook","who let her cook",
    "nah this crazy","nah this wild","this is insane 😭","im actually crying","i’m actually crying"
]

HYPE_KEYS = [
    "lets go","let's go","lfg","fire","so fire","this fire","goat","the goat","crazy","insane","holy","W","big W","huge W",
    "clean","smooth","perfect","elite","top tier","cook","cooked","let him cook","let her cook",
    "this goes hard","hard af","hard asf","this slaps","goes insane","this is fire","this heat","this gas","built different"
]

SAD_KEYS = [
    "sad","im sad","i'm sad","tired","im tired","i'm tired","exhausted","burnt out","drained",
    "upset","cry","crying","depressed","pain","lonely","alone","anxious","stressed","overwhelmed",
    "miserable","im miserable","i'm miserable","this sucks","life sucks","cant do this","i can’t do this",
    "rough day","bad day","long day","im not okay","i'm not okay","not okay"
]

ACK_KEYS = [
    "thanks","thx","ty","thank you","appreciate","appreciate it","got it","gotcha","ok","okay","cool",
    "sounds good","makes sense","fair","bet","noted","all good","alright","for sure","fs","yea","yeah","yep","yup","mm","mhm"
]

AGREE_KEYS = [
    "true","facts","real","fr","frfr","same","exactly","100%","literally","on god","ong",
    "thats right","that's right","you right","u right","correct","absolutely","definitely","this","that part"
]

DISBELIEF_KEYS = [
    "no way","no shot","cap","bs","bullshit","fake","sure buddy","nah","be fr","be serious",
    "you lying","ur lying","you’re lying","theres no way","there's no way","calling cap","stop the cap","not a chance","yeah right"
]

DEFAULT_BUCKETS = {
    "ack": ["👍","👌","✅","☑️","🫡"],
    "see": ["👀","🫣","🧠","📝"],
    "funny": ["😂","😭","💀","🤣","😹"],
    "hype": ["🔥","💯","🚀","🙌","✨"],
    "sad": ["😔","🫂","❤️","😞","🥲"],
    "question": ["❓","🤔","🧐","💭"],
    "agree": ["✅","💯","🤝","👍","🫡"],
    "disbelief": ["🧢","😳","🤨","😐","🙄"]
}

def _has_any(text: str, keys: List[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keys)

def _is_question(content: str) -> bool:
    if not content:
        return False
    t = content.lower()
    if "?" in content and len(content) > 7:
        return True
    if len(t) < 6:
        return False
    return any(t.startswith(k + " ") for k in ("why","how","what","when","where","who","which","wait","hold up"))

def _low_effort(text: str) -> bool:
    t = _norm(text)
    if not t:
        return True
    if t in {"hi","hey","hello","yo","sup"}:
        return False
    if len(t) <= 3:
        return True
    return t in LOW_EFFORT


def _circadian_penalty() -> float:
    lt = time.localtime()
    hour = lt.tm_hour
    wday = lt.tm_wday
    if 2 <= hour <= 6:
        return 0.13
    if hour >= 0 and hour <= 1:
        return 0.08
    if wday >= 5 and hour >= 23:
        return 0.07
    return 0.0

def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def _sigmoid(x: float) -> float:
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))

class BrainStore:
    def __init__(self, path: str):
        self.path = path
        self.last_save = 0.0

    def load(self) -> Dict[str, Any]:
        if not self.path or not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        if not self.path:
            return
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, self.path)
            self.last_save = _now()
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

class HumanBrain:
    def __init__(self, persist_path: str = "human_brain_state.json", is_roast_mode=None):
        self.store = BrainStore(persist_path)
        self._rng = random.Random()
        self._last_channel_time: Dict[int, float] = {}
        self._last_user_time: Dict[int, float] = {}
        self._recent_reacts: Deque[float] = deque()
        self._recent_emojis: Deque[str] = deque(maxlen=REACTION_DIVERSITY_WINDOW)
        self._channel_msgs: Dict[int, Deque[Tuple[float, str]]] = defaultdict(lambda: deque(maxlen=CONTEXT_WINDOW))
        self._channel_culture: Dict[int, Deque[Tuple[float, str]]] = defaultdict(lambda: deque(maxlen=CULTURE_MEMORY_MAX))
        self._channel_emoji_counts: Dict[int, Counter] = defaultdict(Counter)
        self.is_roast_mode = is_roast_mode or (lambda uid: False)
        self._guild_emoji_culture: Dict[int, Counter] = defaultdict(Counter)
        self._guild_emoji_timestamps: Dict[int, Deque[Tuple[float, str]]] = defaultdict(lambda: deque(maxlen=2000))
        self._user_familiarity: Dict[int, int] = defaultdict(int)
        self._user_channel_affinity: Dict[Tuple[int, int], int] = defaultdict(int)
        self._user_recent_emoji: Dict[int, Deque[str]] = defaultdict(lambda: deque(maxlen=10))
        self._user_emoji_pref: Dict[int, Counter] = defaultdict(Counter)
        self._user_received_reacts: Dict[int, int] = defaultdict(int)
        self._user_given_reacts: Dict[int, int] = defaultdict(int)
        self._moods = ["neutral", "warm", "tired", "silly", "focused"]
        self._self_react_memory: Dict[int, float] = {} 
        self._pending_react_back: Dict[Tuple[int, int], Tuple[float, str]] = {}
        self._pending_self_reacts: Deque[Tuple[float, int, int, str]] = deque()
        self._seen_messages: Deque[int] = deque(maxlen=500)
        self._current_mood = self._rng.choice(self._moods)
        self._channel_state: Dict[int, str] = defaultdict(lambda: STATE_LURKING)
        self._last_speak_time: Dict[int, float] = {}
        self._last_speak_confidence: Dict[int, float] = defaultdict(lambda: 0.56)
        self._last_channel_embarrassment: Dict[int, float] = defaultdict(float)
        self._delayed_reacts: Deque[Tuple[float, int, int, int, str]] = deque()
        self._react_outcomes_user: Dict[int, Deque[Tuple[float, str, int]]] = defaultdict(lambda: deque(maxlen=120))
        self._interject_outcomes_channel: Dict[int, Deque[Tuple[float, int]]] = defaultdict(lambda: deque(maxlen=120))
        self._channel_profile: Dict[int, Dict[str, float]] = defaultdict(lambda: {
            "formality": 0.45,
            "emoji_tolerance": 0.55,
            "chaos": 0.45,
            "boldness": 1.0
        })
        self._guild_profile: Dict[int, Dict[str, float]] = defaultdict(lambda: {
            "boldness": 1.0
        })
        self._last_reflect = _now()
        self._last_persist = _now()
        self._load()
    def mark_busy(self, channel_id: int) -> None:
        self._last_speak_time[channel_id] = _now()

    def _load(self) -> None:
        data = self.store.load()
        if not data:
            return
        try:
            self._current_mood = data.get("mood", self._current_mood)
            gp = data.get("guild_profile", {})
            for k, v in gp.items():
                try:
                    gid = int(k)
                    if isinstance(v, dict):
                        self._guild_profile[gid].update({kk: float(vv) for kk, vv in v.items()})
                except Exception:
                    pass
            cp = data.get("channel_profile", {})
            for k, v in cp.items():
                try:
                    cid = int(k)
                    if isinstance(v, dict):
                        self._channel_profile[cid].update({kk: float(vv) for kk, vv in v.items()})
                except Exception:
                    pass
            up = data.get("user_emoji_pref", {})
            for k, v in up.items():
                try:
                    uid = int(k)
                    if isinstance(v, dict):
                        c = Counter()
                        for ek, ev in v.items():
                            c[ek] = int(ev)
                        self._user_emoji_pref[uid] = c
                except Exception:
                    pass
            uf = data.get("user_familiarity", {})
            for k, v in uf.items():
                try:
                    uid = int(k)
                    self._user_familiarity[uid] = int(v)
                except Exception:
                    pass
            ucr = data.get("user_received_reacts", {})
            for k, v in ucr.items():
                try:
                    uid = int(k)
                    self._user_received_reacts[uid] = int(v)
                except Exception:
                    pass
            ucg = data.get("user_given_reacts", {})
            for k, v in ucg.items():
                try:
                    uid = int(k)
                    self._user_given_reacts[uid] = int(v)
                except Exception:
                    pass
            gec = data.get("guild_emoji_culture", {})
            for k, v in gec.items():
                try:
                    gid = int(k)
                    self._guild_emoji_culture[gid] = Counter(v)
                except:
                    pass

        except Exception:
            pass

    def _dump(self) -> Dict[str, Any]:
        gp = {str(gid): dict(v) for gid, v in self._guild_profile.items()}
        cp = {str(cid): dict(v) for cid, v in self._channel_profile.items()}
        up = {str(uid): dict(c) for uid, c in self._user_emoji_pref.items()}
        uf = {str(uid): int(v) for uid, v in self._user_familiarity.items()}
        ucr = {str(uid): int(v) for uid, v in self._user_received_reacts.items()}
        ucg = {str(uid): int(v) for uid, v in self._user_given_reacts.items()}
        return {
            "mood": self._current_mood,
            "guild_profile": gp,
            "channel_profile": cp,
            "user_emoji_pref": up,
            "user_familiarity": uf,
            "user_received_reacts": ucr,
            "user_given_reacts": ucg,
            "guild_emoji_culture": {
                str(gid): dict(c) for gid, c in self._guild_emoji_culture.items()
            }
        }

    def maybe_persist(self) -> None:
        t = _now()
        if t - self._last_persist < PERSIST_EVERY:
            return
        self._last_persist = t
        self.store.save(self._dump())

    def _fatigue_penalty(self) -> float:
        cutoff = _now() - FATIGUE_WINDOW_SEC
        while self._recent_reacts and self._recent_reacts[0] < cutoff:
            self._recent_reacts.popleft()
        return min(len(self._recent_reacts) * FATIGUE_STEP, MAX_FATIGUE_PENALTY)

    def _soft_cooldown_penalty(self, channel_id: int, user_id: int) -> float:
        t = _now()
        dc = t - self._last_channel_time.get(channel_id, 0.0)
        du = t - self._last_user_time.get(user_id, 0.0)
        pc = 0.0 if dc >= SOFT_COOLDOWN_CHANNEL else (1.0 - dc / SOFT_COOLDOWN_CHANNEL) * 0.20
        pu = 0.0 if du >= SOFT_COOLDOWN_USER else (1.0 - du / SOFT_COOLDOWN_USER) * 0.25
        return pc + pu

    def _cooldown_hard(self, channel_id: int, user_id: int) -> bool:
        t = _now()
        if t - self._last_channel_time.get(channel_id, 0.0) < HARD_MIN_GAP_CHANNEL:
            return True
        if t - self._last_user_time.get(user_id, 0.0) < HARD_MIN_GAP_USER:
            return True
        return False
    async def process_self_reacts(self, bot: discord.Client) -> None:
        if not self._pending_self_reacts:
            return

        now = _now()
        keep = deque()
        cutoff = _now() - 3600
        self._self_react_memory = {
            mid: ts for mid, ts in self._self_react_memory.items()
            if ts > cutoff
        }

        while self._pending_self_reacts:
            when, cid, mid, emoji = self._pending_self_reacts.popleft()
            if when > now:
                keep.append((when, cid, mid, emoji))
                continue

            try:
                for guild in bot.guilds:
                    ch = guild.get_channel(cid)
                    if not ch:
                        continue
                    try:
                        msg = await ch.fetch_message(mid)
                    except Exception:
                        continue
                    await msg.add_reaction(emoji)
                    self._mark_react(cid, msg.author.id, emoji, guild.id)
                    self._pending_react_back[(reactor_id, message_id)] = (_now(), emoji)

                    break
            except Exception:
                pass

        self._pending_self_reacts = keep


    def maybe_ack_reaction_on_self(
        self,
        channel_id: int,
        reactor_id: int,
        emoji: str,
        message_id: int,
    ) -> None:
        now = _now()

        if message_id in self._self_react_memory:
            return

        conf = self._last_speak_confidence[channel_id]
        emb = self._last_channel_embarrassment[channel_id]
        fam = self._user_familiarity[reactor_id]
        st = self._channel_state[channel_id]
    
        p = 0.025 

        if fam > 6:
            p += 0.04

        if emoji in ("😂", "😭", "💀", "🤣"):
            p += 0.04

        if conf > 0.60:
            p += 0.03

        if emb > 0.5 or st == STATE_WITHDRAWING:
            return

        if self._rng.random() > min(p, 0.12):
            return

        delay = self._rng.uniform(3.0, 10.0)
        self.observe_received_reaction(reactor_id)
        self._self_react_memory[message_id] = now
        self._pending_self_reacts.append(
            (now + delay, channel_id, message_id, emoji)
        )

    def observe_channel_message(self, channel_id: int, content: str, msg_id: Optional[int] = None) -> None:
        if msg_id is not None:
            if msg_id in self._seen_messages:
                return
            self._seen_messages.append(msg_id)

        if not content:
            return
        self._channel_msgs[channel_id].append((_now(), content))
        self._update_channel_profile_from_text(channel_id, content)

    def observe_reaction(self, channel_id: int, user_id: int, emoji: str, guild_id: Optional[int] = None) -> None:
        if not emoji:
            return
        self._culture_decay(channel_id)
        t = _now()
        self._channel_culture[channel_id].append((t, emoji))
        self._channel_emoji_counts[channel_id][emoji] += 1
        self._user_emoji_pref[user_id][emoji] += 1
        self._user_given_reacts[user_id] += 1
        if guild_id:
            self._guild_emoji_culture[guild_id][emoji] += 1
            self._guild_emoji_timestamps[guild_id].append((_now(), emoji))


    def observe_received_reaction(self, user_id: int) -> None:
        self._user_received_reacts[user_id] += 1

    def observe_reaction_outcome(self, user_id: int, emoji: str, got_back: bool) -> None:
        t = _now()
        self._react_outcomes_user[user_id].append((t, emoji, 1 if got_back else 0))
    def observe_reaction_back_from_event(self, reactor_id: int, message_id: int):
        key = (reactor_id, message_id)
        pending = self._pending_react_back.get(key)
        if not pending:
            return

        ts, emoji = pending
        age = _now() - ts
        got_back = 0.6 <= age <= 25.0

        self.observe_reaction_outcome(reactor_id, emoji, got_back)
        del self._pending_react_back[key]


    def observe_interject_outcome(self, channel_id: int, got_reply: bool) -> None:
        t = _now()
        self._interject_outcomes_channel[channel_id].append((t, 1 if got_reply else 0))

    def _culture_decay(self, channel_id: int) -> None:
        t = _now()
        dq = self._channel_culture[channel_id]
        while dq:
            ts, emoji = dq[0]
            if t - ts <= CULTURE_HALF_LIFE_SEC:
                break
            dq.popleft()
            if self._channel_emoji_counts[channel_id][emoji] > 0:
                self._channel_emoji_counts[channel_id][emoji] -= 1
                if self._channel_emoji_counts[channel_id][emoji] <= 0:
                    del self._channel_emoji_counts[channel_id][emoji] 

    def _guild_culture_decay(self, guild_id: int) -> None:
        now = _now()
        dq = self._guild_emoji_timestamps[guild_id]
        counts = self._guild_emoji_culture[guild_id]

        while dq:
            ts, emoji = dq[0]
            if now - ts <= GUILD_EMOJI_HALF_LIFE:
                break
            dq.popleft()
            if counts[emoji] > 0:
                counts[emoji] -= 1
                if counts[emoji] <= 0:
                    del counts[emoji]

    def _guild_top_emojis(self, guild_id: int, k: int = 8) -> List[str]:
        self._guild_culture_decay(guild_id)
        counts = self._guild_emoji_culture[guild_id]
        if not counts:
            return []
        return [e for e, _ in counts.most_common(k)]

    def _culture_top_emojis(self, channel_id: int, k: int = 8) -> List[str]:
        counts = self._channel_emoji_counts[channel_id]
        if not counts:
            return []
        return [e for e, _ in counts.most_common(k)]

    def _diversity_penalty(self, emoji: str) -> float:
        if not self._recent_emojis:
            return 0.0
        repeats = sum(1 for e in self._recent_emojis if e == emoji)
        if repeats <= 0:
            return 0.0
        return min(repeats * (REACTION_REPEAT_PENALTY / 2.0), REACTION_REPEAT_PENALTY)

    def _maybe_shift_mood(self) -> None:
        r = self._rng.random()
        if r < 0.016:
            self._current_mood = self._rng.choice(self._moods)
        elif r < 0.018:
            self._current_mood = "tired"
        elif r < 0.020:
            self._current_mood = "warm"

    def _context_activity(self, channel_id: int) -> float:
        q = self._channel_msgs[channel_id]
        if len(q) < 2:
            return 0.0
        t = _now()
        recent = [ts for ts, _ in q if t - ts <= CONTEXT_ACTIVE_SEC]
        if not recent:
            return 0.0
        density = min(len(recent) / 6.0, 1.0)
        return density

    def _reciprocity_bonus(self, user_id: int) -> float:
        given = self._user_given_reacts.get(user_id, 0)
        received = self._user_received_reacts.get(user_id, 0)
        if given <= 0:
            return 0.0
        ratio = min(received / max(given, 1), 2.0)
        if ratio <= 0.45:
            return 0.0
        return min((ratio - 0.45) * 0.075, 0.10)

    def _reaction_outcome_bias(self, user_id: int, emoji: str) -> float:
        dq = self._react_outcomes_user.get(user_id)
        if not dq:
            return 0.0
        recent = list(dq)[-70:]
        hits = 0
        tot = 0
        for _, e, ok in recent:
            if e == emoji:
                tot += 1
                hits += ok
        if tot <= 3:
            return 0.0
        rate = hits / tot
        return (rate - 0.45) * 0.22

    def _pick_bucket(self, text_l: str, content: str) -> str:
        if _is_question(content):
            return "question"
        if _has_any(text_l, SAD_KEYS):
            return "sad"
        if _has_any(text_l, FUNNY_KEYS):
            return "funny"
        if _has_any(text_l, HYPE_KEYS):
            return "hype"
        if _has_any(text_l, ACK_KEYS):
            return "ack"
        if _has_any(text_l, AGREE_KEYS):
            return "agree"
        if _has_any(text_l, DISBELIEF_KEYS):
            return "disbelief"
        if len(content) > 120:
            return "see"
        return "ack"

    def _mood_tweak_bucket(self, bucket: str) -> str:
        m = self._current_mood
        if m == "tired":
            if bucket in ("funny", "hype"):
                return "see"
            if bucket == "sad":
                return "sad"
            return "see"
        if m == "warm":
            if bucket in ("ack", "agree"):
                return "agree"
            if bucket == "sad":
                return "sad"
            return bucket
        if m == "silly":
            if bucket in ("ack", "agree", "disbelief"):
                return "funny"
            return bucket
        if m == "focused":
            if bucket in ("funny", "hype"):
                return "ack"
            return bucket
        return bucket

    def _candidate_emojis(self, channel_id: int, user_id: int, bucket: str, guild_id: Optional[int] = None) -> List[str]:
        base = list(DEFAULT_BUCKETS.get(bucket, DEFAULT_BUCKETS["ack"]))
        self._culture_decay(channel_id)
        culture = self._culture_top_emojis(channel_id, k=10)
        guild_emojis = self._guild_top_emojis(guild_id, k=6) if guild_id else []
        prefs = [e for e, _ in self._user_emoji_pref[user_id].most_common(7)]
        pool = []
        pool.extend(base)
        pool.extend(culture * 2)   
        pool.extend(guild_emojis)   
        pool.extend(prefs)
        seen = set()
        uniq = []
        for e in pool:
            if e and e not in seen:
                seen.add(e)
                uniq.append(e)
        return uniq[:18] if uniq else base

    def _choose_emoji(self, channel_id: int, user_id: int, bucket: str, guild_id: Optional[int] = None) -> str:
        bucket = self._mood_tweak_bucket(bucket)
        cand = self._candidate_emojis(channel_id, user_id, bucket, guild_id)
        weights = []
        prof = self._channel_profile[channel_id]
        emoji_tol = _clamp(prof.get("emoji_tolerance", 0.55), 0.0, 1.0)
        for e in cand:
            w = 1.0
            w += min(self._user_emoji_pref[user_id].get(e, 0) * 0.055, 0.58)
            w += min(self._channel_emoji_counts[channel_id].get(e, 0) * 0.025, 0.70)
            w += self._reaction_outcome_bias(user_id, e)
            w -= self._diversity_penalty(e)
            if e in self._user_recent_emoji[user_id]:
                w *= 0.56
            if e in self._recent_emojis:
                w *= 0.80
            w *= (0.78 + 0.44 * emoji_tol)
            weights.append(max(w, 0.06))
        total = sum(weights)
        r = self._rng.random() * total if total > 0 else 0.0
        acc = 0.0
        for e, w in zip(cand, weights):
            acc += w
            if r <= acc:
                return e
        return self._rng.choice(cand) if cand else "👍"

    def _mark_react(self, channel_id: int, user_id: int, emoji: str, guild_id: Optional[int] = None) -> None:
        t = _now()
        self._last_channel_time[channel_id] = t
        self._last_user_time[user_id] = t
        self._recent_reacts.append(t)
        self._recent_emojis.append(emoji)
        self._user_recent_emoji[user_id].append(emoji)
        self._user_familiarity[user_id] += 1
        self._user_channel_affinity[(user_id, channel_id)] += 1
        if guild_id:
            self._guild_emoji_culture[guild_id][emoji] += 1
            self._guild_emoji_timestamps[guild_id].append((_now(), emoji))


    def _len_bonus(self, content: str) -> float:
        L = len(content)
        return min(L / 260.0, 0.24)

    def _familiarity_bonus(self, user_id: int) -> float:
        return min(self._user_familiarity[user_id] * 0.010, 0.12)

    def _affinity_bonus(self, user_id: int, channel_id: int) -> float:
        return min(self._user_channel_affinity[(user_id, channel_id)] * 0.0065, 0.07)

    def _link_penalty(self, content: str) -> float:
        if ("http://" in content or "https://" in content) and len(content) < 55:
            return 0.09
        return 0.0

    def _caps_bonus(self, content: str) -> float:
        if len(content) > 6 and content.isupper():
            return 0.045
        return 0.0

    def _channel_boldness(self, guild_id: int, channel_id: int) -> float:
        g = self._guild_profile[guild_id].get("boldness", 1.0)
        c = self._channel_profile[channel_id].get("boldness", 1.0)
        return _clamp(g * c, MIN_CHANNEL_BOLDNESS, MAX_CHANNEL_BOLDNESS)

    def p_react(self, message: discord.Message, mentioned: bool) -> float:
        content = (message.content or "").strip()
        uid = message.author.id
        cid = message.channel.id
        gid = message.guild.id if message.guild else 0
        bold = self._channel_boldness(gid, cid)
        p = BASE_REACT_MENTION if mentioned else BASE_REACT_PASSIVE
        p += self._len_bonus(content)
        p += self._familiarity_bonus(uid)
        p += self._affinity_bonus(uid, cid)
        p += self._reciprocity_bonus(uid)
        p += self._context_activity(cid) * 0.07
        p += self._caps_bonus(content)
        p -= self._fatigue_penalty()
        p -= _circadian_penalty()
        p -= self._soft_cooldown_penalty(cid, uid)
        p -= self._link_penalty(content)
        if message.mentions and not mentioned:
            p += 0.03
        prof = self._channel_profile[cid]
        formality = _clamp(prof.get("formality", 0.45), 0.0, 1.0)
        emoji_tol = _clamp(prof.get("emoji_tolerance", 0.55), 0.0, 1.0)
        chaos = _clamp(prof.get("chaos", 0.45), 0.0, 1.0)
        p *= (0.86 + 0.28 * bold)
        p *= (0.88 + 0.18 * emoji_tol)
        p *= (0.90 + 0.12 * chaos)
        p *= (1.06 - 0.18 * formality)
        if self._current_mood == "tired":
            p *= 0.80
        elif self._current_mood == "silly":
            p *= 1.07
        elif self._current_mood == "warm":
            p *= 1.04
        p = _clamp(p, 0.0, 0.90)
        return p

    async def human_delay(self, channel: discord.abc.Messageable, reply_text: str = "") -> None:
        txt = reply_text or ""
        w = max(len(_words(txt)), 1)
        wpm = self._rng.uniform(*READING_WPM)
        read_time = min(max((w / wpm) * 60.0, READING_MIN), READING_MAX)
        base = self._rng.uniform(*TYPE_BASE)
        per = self._rng.uniform(*TYPE_PER_CHAR)
        type_time = base + min(len(txt) * per, TYPE_MAX)
        total = read_time + type_time
        chunks = max(1, int(total / self._rng.uniform(1.15, 2.0)))
        remaining = total
        for _ in range(chunks):
            d = min(remaining, self._rng.uniform(0.50, 1.55))
            remaining -= d
            try:
                async with channel.typing():
                    await asyncio.sleep(d)
            except Exception:
                await asyncio.sleep(d)
            if self._rng.random() < TYPE_HESITATION_CHANCE:
                await asyncio.sleep(self._rng.uniform(*TYPE_HESITATION_RANGE))

    def _decay_embarrassment(self, channel_id: int) -> None:
        t = _now()
        last = self._last_speak_time.get(channel_id)
        if not last:
            return
        age = t - last
        if age <= 0:
            return
        decay = math.exp(-age / EMBARRASSMENT_HALF_LIFE)
        self._last_channel_embarrassment[channel_id] *= decay

    def _update_channel_state(self, channel_id: int) -> None:
        emb = self._last_channel_embarrassment[channel_id]
        conf = self._last_speak_confidence[channel_id]
        prof = self._channel_profile[channel_id]
        bold = _clamp(prof.get("boldness", 1.0), MIN_CHANNEL_BOLDNESS, MAX_CHANNEL_BOLDNESS)
        if emb > 0.62:
            self._channel_state[channel_id] = STATE_WITHDRAWING
        elif conf > (0.69 - (bold - 1.0) * 0.10):
            self._channel_state[channel_id] = STATE_LEADING
        elif conf > 0.50:
            self._channel_state[channel_id] = STATE_ENGAGED
        else:
            self._channel_state[channel_id] = STATE_LURKING

    def _dynamic_speak_cooldown(self, channel_id: int) -> float:
        st = self._channel_state[channel_id]
        prof = self._channel_profile[channel_id]
        chaos = _clamp(prof.get("chaos", 0.45), 0.0, 1.0)
        formality = _clamp(prof.get("formality", 0.45), 0.0, 1.0)
        base = SPEAK_COOLDOWN_BASE
        if st == STATE_LEADING:
            base = 30.0
        elif st == STATE_ENGAGED:
            base = 44.0
        elif st == STATE_WITHDRAWING:
            base = 95.0
        base *= (0.88 + 0.30 * formality)
        base *= (1.05 - 0.25 * chaos)
        if self._current_mood == "tired":
            base *= 1.15
        elif self._current_mood == "silly":
            base *= 0.90
        return _clamp(base, 18.0, 140.0)

    def _silence_pressure(self, channel_id: int) -> float:
        q = self._channel_msgs[channel_id]
        if not q:
            return 0.30
        last_ts, _ = q[-1]
        age = _now() - last_ts
        if age < 5.5:
            return 0.0
        if age > 38.0:
            return 0.40
        return min((age - 5.5) / (38.0 - 5.5), 1.0) * 0.40

    def _conversation_pressure(self, channel_id: int) -> float:
        q = self._channel_msgs[channel_id]
        if len(q) < 3:
            return 0.0
        t = _now()
        recent = [(ts, msg) for ts, msg in q if t - ts < 50.0]
        if len(recent) < 3:
            return 0.0
        lengths = [len(m) for _, m in recent]
        avg_len = sum(lengths) / len(lengths)
        density = min(len(recent) / 7.0, 1.0)
        emo = 0.0
        for _, m in recent:
            ml = m.lower()
            emo += 0.06 if "??" in m else 0.0
            emo += 0.05 if "wtf" in ml else 0.0
            emo += 0.04 if "bro" in ml or "bruh" in ml else 0.0
            emo += 0.03 if "nah" in ml else 0.0
        return min(density * 0.30 + min(avg_len / 160.0, 0.20) + min(emo, 0.22), 0.70)

    def _unanswered_question_pressure(self, channel_id: int) -> float:
        q = self._channel_msgs[channel_id]
        if not q:
            return 0.0
        ts, msg = q[-1]
        if not _is_question(msg):
            return 0.0
        age = _now() - ts
        if age < 3.8 or age > 36.0:
            return 0.0
        return min((age - 3.8) / (36.0 - 3.8), 1.0) * 0.55

    def _relevance_pressure(self, message: discord.Message) -> float:
        uid = message.author.id
        cid = message.channel.id
        sc = 0.0
        sc += min(self._user_channel_affinity[(uid, cid)] * 0.025, 0.16)
        sc += min(self._user_familiarity[uid] * 0.018, 0.13)
        return sc

    def _confidence_decay(self, channel_id: int) -> float:
        base = self._last_speak_confidence[channel_id]
        decay = 1.0 - min(self._last_channel_embarrassment[channel_id], 0.88)
        return max(base * decay, 0.22)

    def _interject_success_bias(self, channel_id: int) -> float:
        dq = self._interject_outcomes_channel.get(channel_id)
        if not dq:
            return 0.0
        recent = list(dq)[-70:]
        if len(recent) < 8:
            return 0.0
        rate = sum(v for _, v in recent) / len(recent)
        return (rate - 0.45) * 0.22

    def _social_risk(self, channel_id: int) -> float:
        emb = self._last_channel_embarrassment[channel_id]
        fat = self._fatigue_penalty()
        circ = _circadian_penalty()
        st = self._channel_state[channel_id]
        risk = emb * 0.70 + fat * 0.65 + circ * 0.55
        if st == STATE_WITHDRAWING:
            risk += 0.12
        if self._current_mood == "tired":
            risk += 0.08
        return _clamp(risk, 0.0, 1.0)

    def _update_channel_profile_from_text(self, channel_id: int, content: str) -> None:
        prof = self._channel_profile[channel_id]
        t = content or ""
        L = len(t)
        tl = t.lower()
        emoji_count = len(_EMOJI_RE.findall(t))
        punct = t.count("!") + t.count("?")
        caps = 1 if (L > 6 and t.isupper()) else 0
        shorty = 1 if L <= 20 else 0
        linky = 1 if ("http://" in t or "https://" in t) else 0
        slang = 1 if any(x in tl for x in ("bruh","bro","nah","fr","ong","lfg","wtf")) else 0
        laugh = 1 if any(x in tl for x in ("lol","lmao","😂","😭","💀","🤣")) else 0
        formality_target = 0.55
        formality_target += 0.08 * linky
        formality_target += 0.10 * (1 - shorty)
        formality_target -= 0.12 * slang
        formality_target -= 0.08 * laugh
        formality_target -= 0.06 * (emoji_count > 0)
        emoji_tol_target = 0.52
        emoji_tol_target += 0.18 * (emoji_count > 0)
        emoji_tol_target += 0.10 * laugh
        emoji_tol_target -= 0.10 * (formality_target > 0.60)
        chaos_target = 0.45
        chaos_target += 0.12 * (punct >= 2)
        chaos_target += 0.10 * slang
        chaos_target += 0.08 * laugh
        chaos_target += 0.06 * caps
        chaos_target -= 0.08 * linky
        a = 0.020
        prof["formality"] = _clamp((1 - a) * prof.get("formality", 0.45) + a * _clamp(formality_target, 0.0, 1.0), 0.0, 1.0)
        prof["emoji_tolerance"] = _clamp((1 - a) * prof.get("emoji_tolerance", 0.55) + a * _clamp(emoji_tol_target, 0.0, 1.0), 0.0, 1.0)
        prof["chaos"] = _clamp((1 - a) * prof.get("chaos", 0.45) + a * _clamp(chaos_target, 0.0, 1.0), 0.0, 1.0)

    def set_guild_boldness(self, guild_id: int, boldness: float) -> None:
        self._guild_profile[guild_id]["boldness"] = _clamp(boldness, 0.50, 1.60)

    def set_channel_boldness(self, channel_id: int, boldness: float) -> None:
        self._channel_profile[channel_id]["boldness"] = _clamp(boldness, MIN_CHANNEL_BOLDNESS, MAX_CHANNEL_BOLDNESS)

    def queue_delayed_react(self, when_ts: float, guild_id: int, channel_id: int, user_id: int, message_id: int, emoji: str) -> None:
        self._delayed_reacts.append((when_ts, guild_id, channel_id, user_id, message_id, emoji))

    def _should_queue_late_react(self, channel_id: int, bucket: str, content: str) -> bool:
        prof = self._channel_profile[channel_id]
        chaos = _clamp(prof.get("chaos", 0.45), 0.0, 1.0)
        emoji_tol = _clamp(prof.get("emoji_tolerance", 0.55), 0.0, 1.0)
        base = 0.030
        if bucket in ("funny","hype"):
            base += 0.035
        if "😂" in content or "😭" in content or "💀" in content:
            base += 0.030
        base *= (0.85 + 0.30 * chaos)
        base *= (0.85 + 0.25 * emoji_tol)
        if self._current_mood == "tired":
            base *= 0.75
        return self._rng.random() < _clamp(base, 0.0, 0.16)

    def _should_scroll_past(self, channel_id: int) -> bool:
        a = self._context_activity(channel_id)
        miss = 0.05 + a * 0.035
        if self._current_mood == "tired":
            miss += 0.06
        if self._channel_state[channel_id] == STATE_WITHDRAWING:
            miss += 0.04
        return self._rng.random() < miss

    async def maybe_react(self, message: discord.Message, mentioned: bool = False) -> Optional[Dict[str, Any]]:
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.content and message.content[0] in IGNORE_PREFIXES:
            return
        if self._cooldown_hard(message.channel.id, message.author.id):
            return
        content = (message.content or "").strip()
        if not content or _low_effort(content):
            return
        self._maybe_shift_mood()
        self.observe_channel_message(message.channel.id, content, message.id)
        self._update_channel_state(message.channel.id)
        if self._should_scroll_past(message.channel.id):
            return
        p = self.p_react(message, mentioned)
        if self._rng.random() > p:
            bucket = self._pick_bucket(content.lower(), content)
            if self._should_queue_late_react(message.channel.id, bucket, content):
                emoji = self._choose_emoji(
                    message.channel.id,
                    message.author.id,
                    bucket,
                    message.guild.id
                )
                delay = self._rng.uniform(1.6, 9.0) * (0.9 + 0.4 * self._channel_profile[message.channel.id].get("chaos", 0.45))
                self.queue_delayed_react(_now() + delay, message.guild.id, message.channel.id, message.author.id, message.id, emoji)
            return
        bucket = self._pick_bucket(content.lower(), content)
        emoji = self._choose_emoji(
            message.channel.id,
            message.author.id,
            bucket,
            message.guild.id
        )

        prof = self._channel_profile[message.channel.id]
        formality = _clamp(prof.get("formality", 0.45), 0.0, 1.0)
        if formality > 0.68 and bucket in ("funny","hype","disbelief"):
            if self._rng.random() < 0.55:
                bucket = "ack"
                emoji = self._choose_emoji(
                    message.channel.id,
                    message.author.id,
                    bucket,
                    message.guild.id
                )

        try:
            await message.add_reaction(emoji)
            self._mark_react(message.channel.id, message.author.id, emoji, message.guild.id)
            self._pending_react_back[(reactor_id, message_id)] = (_now(), emoji)
            if self._rng.random() < REGRET_CHANCE and self._social_risk(message.channel.id) > 0.58:
                delay = self._rng.uniform(*REGRET_DELAY_RANGE)
                return {
                    "type": "regret_react",
                    "delay": delay,
                    "channel_id": message.channel.id,
                    "message_id": message.id,
                    "emoji": emoji,
                }
        except Exception:
            return
        return None


    async def process_delayed_reacts(self, bot: discord.Client) -> None:
        if not self._delayed_reacts:
            return
        t = _now()
        keep: Deque[Tuple[float, int, int, int, int, str]] = deque()
        while self._delayed_reacts:
            when_ts, gid, cid, uid, mid, emoji = self._delayed_reacts.popleft()
            if when_ts > t:
                keep.append((when_ts, gid, cid, uid, mid, emoji))
                continue
            try:
                guild = bot.get_guild(gid)
                if not guild:
                    continue
                ch = guild.get_channel(cid)
                if not ch:
                    continue
                try:
                    msg = await ch.fetch_message(mid)
                except Exception:
                    continue
                if msg.author.bot:
                    continue
                if self._cooldown_hard(cid, uid):
                    continue
                prof = self._channel_profile[cid]
                if self._social_risk(cid) > 0.70 and prof.get("formality", 0.45) > 0.65:
                    continue
                await msg.add_reaction(emoji)
                self._mark_react(cid, uid, emoji, gid)
                self._pending_react_back[(uid, mid)] = (_now(), emoji)
            except Exception:
                continue
        self._delayed_reacts = keep

    def should_interject_probability(self, message: discord.Message) -> float:
        if not message.guild:
            return 0.0
        if message.author.bot:
            return 0.0
        cid = message.channel.id
        uid = message.author.id
        self._decay_embarrassment(cid)
        self._update_channel_state(cid)
        cooldown = self._dynamic_speak_cooldown(cid)
        last = self._last_speak_time.get(cid, 0.0)
        if _now() - last < cooldown:
            return 0.0
        content = (message.content or "")
        cp = self._conversation_pressure(cid)
        qp = self._unanswered_question_pressure(cid)
        rp = self._relevance_pressure(message)
        sp = self._silence_pressure(cid)
        pressure = cp + qp + rp + sp
        if _is_question(content):
            pressure += 0.38
        prof = self._channel_profile[cid]
        chaos = _clamp(prof.get("chaos", 0.45), 0.0, 1.0)
        emoji_tol = _clamp(prof.get("emoji_tolerance", 0.55), 0.0, 1.0)
        formality = _clamp(prof.get("formality", 0.45), 0.0, 1.0)
        st = self._channel_state[cid]
        if st == STATE_LEADING:
            pressure += 0.07
        elif st == STATE_ENGAGED:
            pressure += 0.04
        elif st == STATE_WITHDRAWING:
            pressure -= 0.14
        pressure += chaos * 0.08
        pressure += emoji_tol * 0.03
        pressure -= formality * 0.10
        pressure += self._interject_success_bias(cid)
        fat = self._fatigue_penalty()
        circ = _circadian_penalty()
        emb = self._last_channel_embarrassment[cid] * 0.62
        pressure -= fat
        pressure -= circ
        pressure -= emb
        if self._current_mood == "tired":
            pressure *= 0.62
        elif self._current_mood == "silly":
            pressure *= 1.22
        elif self._current_mood == "focused":
            pressure *= 0.90
        conf = self._confidence_decay(cid)
        gid = message.guild.id
        bold = self._channel_boldness(gid, cid)
        p = BASE_INTERRUPT_PROB + pressure * conf
        p *= (0.88 + 0.30 * bold)
        risk = self._social_risk(cid)
        if risk > 0.72:
            p *= 0.55
        elif risk > 0.55:
            p *= 0.78
        p = _clamp(p, 0.0, MAX_INTERRUPT_PROB)
        return p

    def mark_interjected(self, channel_id: int, success_hint: Optional[bool] = None) -> None:
        t = _now()
        self._last_speak_time[channel_id] = t
        self._decay_embarrassment(channel_id)
        conf = self._confidence_decay(channel_id)
        prof = self._channel_profile[channel_id]
        chaos = _clamp(prof.get("chaos", 0.45), 0.0, 1.0)
        formality = _clamp(prof.get("formality", 0.45), 0.0, 1.0)
        boost = self._rng.uniform(0.04, 0.10)
        if success_hint is True:
            boost += 0.05
        elif success_hint is False:
            boost -= 0.03
        boost *= (0.95 + 0.18 * chaos)
        boost *= (1.02 - 0.18 * formality)
        self._last_speak_confidence[channel_id] = _clamp(conf + boost, 0.22, 0.88)
        emb_add = self._rng.uniform(0.06, 0.16)
        if success_hint is False:
            emb_add += 0.10
        if success_hint is True:
            emb_add -= 0.03
        self._last_channel_embarrassment[channel_id] = _clamp(self._last_channel_embarrassment[channel_id] + emb_add, 0.0, 1.2)
        self._update_channel_state(channel_id)

    def self_reflect(self) -> None:
        t = _now()
        if t - self._last_reflect < SELF_REFLECT_EVERY:
            return
        self._last_reflect = t
        avg_fat = self._fatigue_penalty()
        mood = self._current_mood
        if avg_fat > 0.26 and mood != "tired":
            if self._rng.random() < 0.42:
                self._current_mood = "tired"
        if avg_fat < 0.12 and mood == "tired":
            if self._rng.random() < 0.35:
                self._current_mood = self._rng.choice(["neutral","warm","focused"])
        for cid, dq in list(self._interject_outcomes_channel.items()):
            recent = list(dq)[-60:]
            if len(recent) < 10:
                continue
            rate = sum(v for _, v in recent) / len(recent)
            prof = self._channel_profile[cid]
            b = prof.get("boldness", 1.0)
            if rate > 0.58:
                b = _clamp(b + 0.04, MIN_CHANNEL_BOLDNESS, MAX_CHANNEL_BOLDNESS)
            elif rate < 0.38:
                b = _clamp(b - 0.05, MIN_CHANNEL_BOLDNESS, MAX_CHANNEL_BOLDNESS)
            prof["boldness"] = b

class InterjectTemplates:
    def __init__(self):
        self.neutral = [
            "yeah that makes sense",
            "honestly fair",
            "i was thinking the same",
            "that tracks",
            "lowkey agree",
            "true though",
            "not wrong",
            "valid point",
            "i see what you mean"
        ]
        self.question = [
            "wait why though",
            "how did that happen",
            "what made you think that",
            "can you explain that a bit",
            "what do you mean exactly",
            "wait how",
            "what’s the context",
            "how so"
        ]
        self.funny = [
            "nahhh 💀",
            "bro 😭",
            "this is wild",
            "i’m crying",
            "no way 😭",
            "why is this funny",
            "that’s insane",
            "this took me out"
        ]
        self.hype = [
            "nah that’s huge",
            "that’s fire",
            "W",
            "big W",
            "let him cook",
            "that’s clean",
            "goes hard",
            "built different"
        ]
        self.sad = [
            "damn that sucks",
            "sorry you’re dealing with that",
            "that’s rough",
            "hope it gets better",
            "that’s a lot",
            "i feel that",
            "sending good vibes"
        ]
        self.disbelief = [
            "no shot",
            "ain’t no way",
            "cap",
            "that can’t be real",
            "you’re kidding",
            "nahhhh",
            "that’s crazy if true"
        ]

    def pick(self, bucket: str, rng: random.Random) -> str:
        pool = getattr(self, bucket, None)
        if not pool:
            pool = self.neutral
        return rng.choice(pool)


class SignalStack:
    def __init__(self):
        self.neg_words = {
            "bad","worse","worst","sad","tired","exhausted","upset","angry","mad",
            "depressed","lonely","anxious","stressed","overwhelmed","miserable"
        }
        self.pos_words = {
            "good","great","awesome","nice","amazing","love","happy","excited",
            "fire","clean","perfect","goat","elite","solid"
        }

    def score(self, text: str) -> Dict[str, float]:
        t = text.lower()
        w = _words(t)
        s = defaultdict(float)
        s["length"] = min(len(text) / 220.0, 1.0)
        s["questions"] = t.count("?")
        s["exclaim"] = t.count("!")
        s["emoji"] = sum(1 for c in text if ord(c) > 10000)
        s["laugh"] = sum(1 for k in ("lol","lmao","😂","😭","💀","🤣") if k in t)
        s["neg"] = sum(1 for x in w if x in self.neg_words)
        s["pos"] = sum(1 for x in w if x in self.pos_words)
        s["caps"] = 1.0 if len(text) > 6 and text.isupper() else 0.0
        return s

    def bucket(self, text: str) -> str:
        s = self.score(text)
        if s["questions"] > 0:
            return "question"
        if s["neg"] > 0 and s["pos"] == 0:
            return "sad"
        if s["laugh"] > 0:
            return "funny"
        if s["pos"] > 0 and s["exclaim"] > 0:
            return "hype"
        if s["caps"] > 0:
            return "disbelief"
        return "neutral"


class InterjectionEngine:
    def __init__(self, brain: HumanBrain):
        self.brain = brain
        self.templates = InterjectTemplates()
        self.signals = SignalStack()

    async def maybe_interject(self, message: discord.Message) -> Optional[str]:
        if self.brain.is_roast_mode(message.author.id):
            return None

        p = self.brain.should_interject_probability(message)
        roll = self.brain._rng.random()
        hlog("INTERJECT check", "p=", round(p,3), "roll=", round(roll,3), "msg=", message.content)
        if roll > p:
            return None
        bucket = self.signals.bucket(message.content or "")
        hlog("INTERJECT calling ai_interject_line")
        text = await ai_interject_line(bucket, message.content or "")
        if not text:
            hlog("INTERJECT AI returned empty, using template")
            text = self.templates.pick(bucket, self.brain._rng)
        else:
            hlog("INTERJECT AI returned:", repr(text))

        await self.brain.human_delay(message.channel, text)
        try:
            self.brain.mark_busy(message.channel.id)
            await message.channel.send(text)
            self.brain.observe_channel_message(message.channel.id, text)
            self.brain.mark_interjected(message.channel.id, success_hint=None)
            return text

        except Exception:
            self.brain.mark_interjected(message.channel.id, success_hint=False)
            return None


class OutcomeTracker:
    def __init__(self, brain: HumanBrain):
        self.brain = brain
        self._pending_interjects: Dict[int, float] = {}
    def process_timeouts(self):
        now = _now()
        expired = []

        for cid, ts in self._pending_interjects.items():
            if now - ts > 30.0:  
                self.brain.observe_interject_outcome(cid, False)
                expired.append(cid)

        for cid in expired:
            del self._pending_interjects[cid]
    def note_interject(self, channel_id: int):
        self._pending_interjects[channel_id] = _now()

    def observe_message(self, message: discord.Message):
        if message.author.bot:
            return
        cid = message.channel.id
        if cid not in self._pending_interjects:
            return
        age = _now() - self._pending_interjects[cid]
        if age < 1.0:
            return
        self.brain.observe_interject_outcome(cid, True)
        del self._pending_interjects[cid]


class BrainRuntime:
    def __init__(
        self,
        bot: discord.Client,
        chat_fn: Callable[[str], Awaitable[Optional[str]]],
        roast_fn: Callable[[str, int, str], Awaitable[Optional[str]]],
        get_roast_mode: Callable[[int], Optional[str]],
        persist_path: str = "human_brain_state.json",
        is_roast_mode=None,
    ):
        self._pending_regrets: Deque[Tuple[float, int, int, int, str]] = deque()
        self.bot = bot
        self.chat_fn = chat_fn
        self.roast_fn = roast_fn
        self.get_roast_mode = get_roast_mode
        self.brain = HumanBrain(
            persist_path=persist_path,
            is_roast_mode=is_roast_mode
        )
        self.interjector = InterjectionEngine(self.brain)
        self.outcomes = OutcomeTracker(self.brain)
        self._task_started = False
    async def on_reaction_add(
        self,
        reaction: discord.Reaction,
        user: discord.User,
    ):
        if user.bot:
            return

        msg = reaction.message
        if not msg:
            return

        if not msg.author or msg.author.id != self.bot.user.id:
            return

        self.brain.observe_reaction_back_from_event(user.id, reaction.message.id)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        explicit = self.bot.user in message.mentions if self.bot.user else False
        alias = mentions_fusbot(message.content)

        mentioned = explicit or alias


        result = await self.brain.maybe_react(message, mentioned=mentioned)

        if result and result.get("type") == "regret_react":
            when = _now() + result["delay"]
            self._pending_regrets.append(
                (when, message.guild.id, result["channel_id"], result["message_id"], result["emoji"])
            )

        if mentioned:
            uid = message.author.id

            mode = self.get_roast_mode(uid)

            if mode:
                reply = await self.roast_fn(message.content, uid, mode)
            else:
                reply = await self.chat_fn(message.content)

            if reply:
                await self.brain.human_delay(message.channel, reply)
                await message.channel.send(reply)
                self.brain.mark_busy(message.channel.id)
            return
        reply = await self.interjector.maybe_interject(message)
        if reply is not None:
            self.outcomes.note_interject(message.channel.id)
        self.outcomes.observe_message(message)
        self.brain.self_reflect()
        self.brain.maybe_persist()
    async def process_regrets(self):
        now = time.time()
        keep = deque()

        while self._pending_regrets:
            when, gid, cid, mid, emoji = self._pending_regrets.popleft()
            if when > now:
                keep.append((when, gid, cid, mid, emoji))
                continue
            try:
                guild = self.bot.get_guild(gid)
                if not guild:
                    continue
                ch = guild.get_channel(cid)
                if not ch:
                    continue
                msg = await ch.fetch_message(mid)
                me = guild.get_member(self.bot.user.id)
                if self.brain._social_risk(cid) < self.brain._rng.uniform(0.35, 0.55):
                    continue
                if me:
                    await msg.remove_reaction(emoji, me)
            except Exception:
                pass
    
        self._pending_regrets = keep

    async def background_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.brain.process_delayed_reacts(self.bot)
                await self.brain.process_self_reacts(self.bot)
                await self.process_regrets()
                self.outcomes.process_timeouts()
                self.brain.self_reflect()
                self.brain.maybe_persist()
            except Exception:
                pass
            await asyncio.sleep(1.2)

    def start(self):
        if self._task_started:
            return
        self._task_started = True
        self.bot.loop.create_task(self.background_loop())
