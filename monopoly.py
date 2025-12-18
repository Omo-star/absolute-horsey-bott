import json
import math
import os
import random
import sqlite3
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import hashlib
import io
TILENAME: List[str] = []
PRICEBUY: List[int] = []
RENTPRICE: List[int] = []
RRPRICE: List[int] = []
MORTGAGEPRICE: List[int] = []
TENMORTGAGEPRICE: List[int] = []
HOUSEPRICE: List[int] = []
PROPGROUPS: Dict[str, List[int]] = {}
PROPCOLORS: List[str] = []
CCNAME: List[str] = []
CHANCENAME: List[str] = []

TILENAME[:] = [
    "GO","Mediterranean Avenue","Community Chest","Baltic Avenue","Income Tax",
    "Reading Railroad","Oriental Avenue","Chance","Vermont Avenue","Connecticut Avenue",
    "Jail","St. Charles Place","Electric Company","States Avenue","Virginia Avenue",
    "Pennsylvania Railroad","St. James Place","Community Chest","Tennessee Avenue","New York Avenue",
    "Free Parking","Kentucky Avenue","Chance","Indiana Avenue","Illinois Avenue",
    "B. & O. Railroad","Atlantic Avenue","Ventnor Avenue","Water Works","Marvin Gardens",
    "Go To Jail","Pacific Avenue","North Carolina Avenue","Community Chest","Pennsylvania Avenue",
    "Short Line","Chance","Park Place","Luxury Tax","Boardwalk"
]

PRICEBUY[:] = [
    0,60,0,60,0,200,100,0,100,120,
    0,140,150,140,160,200,180,0,180,200,
    0,220,0,220,240,200,260,260,150,280,
    0,300,300,0,320,200,0,350,0,400
]

HOUSEPRICE[:] = [
    0,50,0,50,0,0,50,0,50,50,
    0,100,0,100,100,0,100,0,100,100,
    0,150,0,150,150,0,150,150,0,150,
    0,200,200,0,200,0,0,200,0,200
]

RENTPRICE[:] = [
    -1,-1,-1,-1,-1,-1,
    2,10,30,90,160,250,
    -1,-1,-1,-1,-1,-1,
    4,20,60,180,320,450,
    -1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,
    6,30,90,270,400,550,
    -1,-1,-1,-1,-1,-1,
    6,30,90,270,400,550,
    8,40,100,300,450,600,
    -1,-1,-1,-1,-1,-1,
    10,50,150,450,625,750,
    -1,-1,-1,-1,-1,-1,
    10,50,150,450,625,750,
    12,60,180,500,700,900,
    -1,-1,-1,-1,-1,-1,
    14,70,200,550,750,950,
    -1,-1,-1,-1,-1,-1,
    14,70,200,550,750,950,
    16,80,220,600,800,1000,
    -1,-1,-1,-1,-1,-1,
    18,90,250,700,875,1050,
    -1,-1,-1,-1,-1,-1,
    18,90,250,700,875,1050,
    -1,-1,-1,-1,-1,-1,
    20,100,300,750,925,1100,
    22,110,330,800,975,1150,
    -1,-1,-1,-1,-1,-1,
    22,110,330,800,975,1150,
    24,120,360,850,1025,1200,
    -1,-1,-1,-1,-1,-1,
    26,130,390,900,1100,1275,
    26,130,390,900,1100,1275,
    -1,-1,-1,-1,-1,-1,
    28,150,450,1000,1200,1400,
    -1,-1,-1,-1,-1,-1,
    -1,-1,-1,-1,-1,-1,
    35,175,500,1100,1300,1500,
    -1,-1,-1,-1,-1,-1,
    50,200,600,1400,1700,2000
]

RRPRICE[:] = [0,25,50,100,200]

MORTGAGEPRICE[:] = [
    0,30,0,30,0,100,50,0,50,60,
    0,70,75,70,80,100,90,0,90,100,
    0,110,0,110,120,100,130,130,75,140,
    0,150,150,0,160,100,0,175,0,200
]

TENMORTGAGEPRICE[:] = [
    0,33,0,33,0,110,55,0,55,66,
    0,77,83,77,88,110,99,0,99,110,
    0,121,0,121,132,110,143,143,83,154,
    0,165,165,0,176,110,0,193,0,220
]

PROPCOLORS[:] = [
    "", "brown","", "brown","",
    "rr","lightblue","", "lightblue","lightblue",
    "", "pink","utility","pink","pink",
    "rr","orange","", "orange","orange",
    "", "red","", "red","red",
    "rr","yellow","yellow","utility","yellow",
    "", "green","green","", "green",
    "rr","", "darkblue","", "darkblue"
]

PROPGROUPS.clear()
PROPGROUPS.update({
    "brown": [1,3],
    "lightblue": [6,8,9],
    "pink": [11,13,14],
    "orange": [16,18,19],
    "red": [21,23,24],
    "yellow": [26,27,29],
    "green": [31,32,34],
    "darkblue": [37,39]
})

CCNAME[:] = [
    "Advance to GO",
    "Bank error in your favor",
    "Doctor's fees",
    "Sale of stock",
    "Get Out of Jail Free",
    "Go to Jail",
    "Grand Opera opening",
    "Holiday fund matures",
    "Income tax refund",
    "Life insurance matures",
    "Hospital fees",
    "School fees",
    "Consultancy fee",
    "Street repairs",
    "You have won second prize",
    "You inherit $100",
    "Birthday gifts"
]

CHANCENAME[:] = [
    "Advance to GO",
    "Advance to Illinois Avenue",
    "Advance to St. Charles Place",
    "Advance to nearest Utility",
    "Advance to nearest Railroad",
    "Bank pays you dividend",
    "Get Out of Jail Free",
    "Go back three spaces",
    "Go to Jail",
    "Street repairs",
    "Pay poor tax",
    "Take a ride on the Reading",
    "Take a walk on Boardwalk",
    "Chairman of the Board",
    "Building loan matures",
    "Crossword competition"
]


def _tables_ready() -> None:
    need = [
        ("TILENAME", TILENAME, 40),
        ("PRICEBUY", PRICEBUY, 40),
        ("RENTPRICE", RENTPRICE, 40 * 6),
        ("RRPRICE", RRPRICE, 5),
        ("MORTGAGEPRICE", MORTGAGEPRICE, 40),
        ("TENMORTGAGEPRICE", TENMORTGAGEPRICE, 40),
        ("HOUSEPRICE", HOUSEPRICE, 40),
        ("PROPCOLORS", PROPCOLORS, 40),
        ("CCNAME", CCNAME, 17),
        ("CHANCENAME", CHANCENAME, 16),
    ]
    for name, arr, n in need:
        if not isinstance(arr, list) or len(arr) < n:
            raise RuntimeError(f"Missing/invalid table: {name} (need list length >= {n})")
    if not isinstance(PROPGROUPS, dict) or not PROPGROUPS:
        raise RuntimeError("Missing/invalid PROPGROUPS (need non-empty dict[str, list[int]])")


@dataclass
class GameConfig:
    startCash: int = 1500
    doMention: bool = False
    incomeValue: int = 200
    luxuryValue: int = 100
    doAuction: bool = True
    bailValue: int = 50
    maxJailRolls: int = 3
    doDoubleGo: bool = False
    goValue: int = 200
    freeParkingValue: Optional[Union[int, str]] = None
    hotelLimit: int = 12
    houseLimit: int = 32
    timeoutValue: int = 60
    minRaise: int = 1
    darkMode: bool = False
    useThreads: bool = False


@dataclass
class PlayerSlot:
    user_id: int
    is_ai: bool = False
    ai_name: str = "[AI]"
    ai_profile: str = "normal"


@dataclass
class TurnSnapshot:
    p: int
    was_doubles: bool
    num_doubles: int
    rolled: Optional[Tuple[int, int]] = None
    last_move: int = 0


@dataclass
class MonopolyState:
    uid: List[PlayerSlot]
    num: int
    numalive: int
    p: int = 0
    injail: List[bool] = field(default_factory=list)
    tile: List[int] = field(default_factory=list)
    bal: List[int] = field(default_factory=list)
    goojf: List[int] = field(default_factory=list)
    isalive: List[bool] = field(default_factory=list)
    jailturn: List[int] = field(default_factory=list)
    ownedby: List[int] = field(default_factory=list)
    numhouse: List[int] = field(default_factory=list)
    ismortgaged: List[int] = field(default_factory=list)
    freeparkingsum: int = 0
    ccn: int = 0
    ccorder: List[int] = field(default_factory=list)
    chancen: int = 0
    chanceorder: List[int] = field(default_factory=list)
    turn: TurnSnapshot = field(default_factory=lambda: TurnSnapshot(p=0, was_doubles=True, num_doubles=0))

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d)

    @classmethod
    def from_json(cls, s: str) -> "MonopolyState":
        d = json.loads(s)
        d["uid"] = [PlayerSlot(**u) for u in d["uid"]]
        d["turn"] = TurnSnapshot(**d["turn"])
        return cls(**d)


class MonopolyDB:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS games (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, state_json TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS settings (guild_id INTEGER PRIMARY KEY, config_json TEXT)"
        )
        con.commit()
        con.close()

    def save_game(self, channel_id: int, guild_id: int, state: MonopolyState) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO games(channel_id, guild_id, state_json) VALUES(?,?,?) "
            "ON CONFLICT(channel_id) DO UPDATE SET guild_id=excluded.guild_id, state_json=excluded.state_json",
            (channel_id, guild_id, state.to_json()),
        )
        con.commit()
        con.close()

    def load_game(self, channel_id: int) -> Optional[Tuple[int, MonopolyState]]:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute("SELECT guild_id, state_json FROM games WHERE channel_id=?", (channel_id,))
        row = cur.fetchone()
        con.close()
        if not row:
            return None
        gid, s = row
        return int(gid), MonopolyState.from_json(s)

    def delete_game(self, channel_id: int) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute("DELETE FROM games WHERE channel_id=?", (channel_id,))
        con.commit()
        con.close()

    def save_config(self, guild_id: int, cfg: GameConfig) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO settings(guild_id, config_json) VALUES(?,?) "
            "ON CONFLICT(guild_id) DO UPDATE SET config_json=excluded.config_json",
            (guild_id, json.dumps(asdict(cfg))),
        )
        con.commit()
        con.close()

    def load_config(self, guild_id: int) -> GameConfig:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute("SELECT config_json FROM settings WHERE guild_id=?", (guild_id,))
        row = cur.fetchone()
        con.close()
        if not row:
            return GameConfig()
        return GameConfig(**json.loads(row[0]))


@dataclass
class EngineEvent:
    kind: str
    data: Dict[str, Any] = field(default_factory=dict)


class MonopolyEngine:
    def __init__(self, state: MonopolyState, cfg: GameConfig, rng: Optional[random.Random] = None):
        _tables_ready()
        self.s = state
        self.cfg = cfg
        self.rng = rng or random.Random()
        self.events: List[EngineEvent] = []

    @staticmethod
    def new_game(player_slots: List[PlayerSlot], cfg: GameConfig, rng: Optional[random.Random] = None) -> "MonopolyEngine":
        _tables_ready()
        n = len(player_slots)
        if n < 2 or n > 8:
            raise ValueError("Monopoly needs 2-8 players")
        r = rng or random.Random()
        ownedby = [
            -2, -1, -2, -1, -2,
            -1, -1, -2, -1, -1,
            -2, -1, -1, -1, -1,
            -1, -1, -2, -1, -1,
            -2, -1, -2, -1, -1,
            -1, -1, -1, -1, -1,
            -2, -1, -1, -2, -1,
            -1, -2, -1, -2, -1
        ]
        numhouse = [
            -1, 0, -1, 0, -1,
            -1, 0, -1, 0, 0,
            -1, 0, -1, 0, 0,
            -1, 0, -1, 0, 0,
            -1, 0, -1, 0, 0,
            -1, 0, 0, -1, 0,
            -1, 0, 0, -1, 0,
            -1, -1, 0, -1, 0
        ]
        ismortgaged = [
            -1, 0, -1, 0, -1,
            0, 0, -1, 0, 0,
            -1, 0, 0, 0, 0,
            0, 0, -1, 0, 0,
            -1, 0, -1, 0, 0,
            0, 0, 0, 0, 0,
            -1, 0, 0, -1, 0,
            0, -1, 0, -1, 0
        ]
        ccorder = list(range(17))
        chanceorder = list(range(16))
        r.shuffle(ccorder)
        r.shuffle(chanceorder)
        s = MonopolyState(
            uid=player_slots,
            num=n,
            numalive=n,
            p=0,
            injail=[False] * n,
            tile=[0] * n,
            bal=[cfg.startCash] * n,
            goojf=[0] * n,
            isalive=[True] * n,
            jailturn=[-1] * n,
            ownedby=ownedby,
            numhouse=numhouse,
            ismortgaged=ismortgaged,
            freeparkingsum=0,
            ccn=0,
            ccorder=ccorder,
            chancen=0,
            chanceorder=chanceorder,
            turn=TurnSnapshot(p=0, was_doubles=True, num_doubles=0),
        )
        return MonopolyEngine(s, cfg, rng=r)

    def clear_events(self) -> None:
        self.events.clear()

    def cur(self) -> int:
        return self.s.p

    def alive_players(self) -> List[int]:
        return [i for i in range(self.s.num) if self.s.isalive[i]]

    def advance_to_next_player(self) -> None:
        n = self.s.num
        for _ in range(n):
            self.s.p = (self.s.p + 1) % n
            if self.s.isalive[self.s.p]:
                self.s.turn = TurnSnapshot(p=self.s.p, was_doubles=True, num_doubles=0)
                return
        self.s.turn = TurnSnapshot(p=self.s.p, was_doubles=False, num_doubles=0)

    def game_over(self) -> bool:
        return self.s.numalive <= 1

    def winner(self) -> Optional[int]:
        if self.s.numalive != 1:
            return None
        for i in range(self.s.num):
            if self.s.isalive[i]:
                return i
        return None

    def _add_event(self, kind: str, **data: Any) -> None:
        self.events.append(EngineEvent(kind=kind, data=dict(data)))

    def _passed_go(self, pid: int, landed: bool) -> None:
        add = self.cfg.goValue * (2 if (landed and self.cfg.doDoubleGo) else 1)
        self.s.bal[pid] += add
        self._add_event("go_money", pid=pid, amount=add, balance=self.s.bal[pid], landed=landed)

    def roll(self) -> Tuple[int, int]:
        d1 = self.rng.randint(1, 6)
        d2 = self.rng.randint(1, 6)
        self.s.turn.rolled = (d1, d2)
        return d1, d2

    def start_turn_events(self) -> None:
        pid = self.cur()
        self._add_event("turn_start", pid=pid, balance=self.s.bal[pid], tile=self.s.tile[pid], injail=self.s.injail[pid])

    def legal_actions(self) -> List[str]:
        pid = self.cur()
        if not self.s.isalive[pid]:
            return []
        if self.s.bal[pid] < 0:
            return ["trade", "house", "mortgage", "forfeit"]
        if self.s.injail[pid]:
            acts = ["bail"]
            if self.s.jailturn[pid] <= self.cfg.maxJailRolls:
                acts.append("roll")
            if self.s.goojf[pid] > 0:
                acts.append("use_goojf")
            return acts
        if self.s.turn.rolled is None:
            return ["roll", "trade", "house", "mortgage"]
        return ["trade", "house", "mortgage", "end"]

    def jail_roll(self) -> None:
        pid = self.cur()
        if not self.s.injail[pid]:
            raise RuntimeError("not in jail")
        if self.s.jailturn[pid] == -1:
            self.s.jailturn[pid] = 0
        self.s.jailturn[pid] += 1
        if self.s.jailturn[pid] > self.cfg.maxJailRolls:
            self._add_event("jail_forced_bail", pid=pid, bail=self.cfg.bailValue)
            return
        d1, d2 = self.roll()
        self._add_event("rolled", pid=pid, d1=d1, d2=d2, total=d1 + d2, doubles=(d1 == d2))
        if d1 == d2:
            self.s.jailturn[pid] = -1
            self.s.injail[pid] = False
            self._add_event("jail_exit", pid=pid, method="doubles")
            self.land(pid, d1 + d2)

    def pay_bail_and_roll(self) -> None:
        pid = self.cur()
        if not self.s.injail[pid]:
            raise RuntimeError("not in jail")
        self.s.bal[pid] -= self.cfg.bailValue
        self.s.freeparkingsum += self.cfg.bailValue
        self.s.jailturn[pid] = -1
        self.s.injail[pid] = False
        self._add_event("bail_paid", pid=pid, bail=self.cfg.bailValue, balance=self.s.bal[pid])
        d1, d2 = self.roll()
        self._add_event("rolled", pid=pid, d1=d1, d2=d2, total=d1 + d2, doubles=(d1 == d2))
        if d1 == d2:
            self.s.turn.num_doubles += 1
        else:
            self.s.turn.was_doubles = False
        self.land(pid, d1 + d2)

    def use_goojf_and_roll(self) -> None:
        pid = self.cur()
        if self.s.goojf[pid] <= 0:
            raise RuntimeError("no goojf")
        self.s.goojf[pid] -= 1
        self.s.jailturn[pid] = -1
        self.s.injail[pid] = False
        self._add_event("goojf_used", pid=pid, remaining=self.s.goojf[pid])
        d1, d2 = self.roll()
        self._add_event("rolled", pid=pid, d1=d1, d2=d2, total=d1 + d2, doubles=(d1 == d2))
        if d1 == d2:
            self.s.turn.num_doubles += 1
        else:
            self.s.turn.was_doubles = False
        self.land(pid, d1 + d2)

    def normal_roll(self) -> None:
        pid = self.cur()
        if self.s.injail[pid]:
            raise RuntimeError("in jail")
        d1, d2 = self.roll()
        self._add_event("rolled", pid=pid, d1=d1, d2=d2, total=d1 + d2, doubles=(d1 == d2))
        if d1 == d2:
            self.s.turn.num_doubles += 1
        else:
            self.s.turn.was_doubles = False
        if self.s.turn.num_doubles >= 3:
            self.s.tile[pid] = 10
            self.s.injail[pid] = True
            self.s.turn.was_doubles = False
            self._add_event("go_to_jail", pid=pid, reason="three_doubles")
            return
        self.land(pid, d1 + d2)

    def land(self, pid: int, distance: int) -> None:
        prev = self.s.tile[pid]
        new = prev + distance
        passed = new >= 40
        if passed:
            new -= 40
            self._passed_go(pid, landed=(new == 0))
        self.s.tile[pid] = new
        self.s.turn.last_move = distance
        self._add_event("moved", pid=pid, from_tile=prev, to_tile=new, distance=distance, passed_go=passed)
        self._resolve_tile(pid, distance)
        if self.s.bal[pid] < 0:
            self._add_event("debt", pid=pid, balance=self.s.bal[pid])

    def _resolve_tile(self, pid: int, distance: int) -> None:
        t = self.s.tile[pid]
        self._add_event("landed", pid=pid, tile=t, name=(TILENAME[t] if t < len(TILENAME) else str(t)))
        owner = self.s.ownedby[t]
        if owner == pid:
            self._add_event("own_tile", pid=pid, tile=t)
            return
        if self.s.ismortgaged[t] == 1:
            self._add_event("mortgaged_no_rent", pid=pid, tile=t, owner=owner)
            return
        if owner == -2:
            self._resolve_unownable(pid, distance)
            return
        if owner == -1:
            self._add_event("buy_offer", pid=pid, tile=t, price=PRICEBUY[t], balance=self.s.bal[pid])
            return
        if RENTPRICE[t * 6] == -1:
            self._pay_rr_util(pid, owner, t, distance)
        else:
            self._pay_property_rent(pid, owner, t)

    def buy_current_tile(self) -> None:
        pid = self.cur()
        t = self.s.tile[pid]
        if self.s.ownedby[t] != -1:
            raise RuntimeError("tile not buyable now")
        price = PRICEBUY[t]
        if self.s.bal[pid] < price:
            raise RuntimeError("cannot afford")
        self.s.bal[pid] -= price
        self.s.ownedby[t] = pid
        self._add_event("bought", pid=pid, tile=t, price=price, balance=self.s.bal[pid])

    def decline_buy_current_tile(self) -> None:
        pid = self.cur()
        t = self.s.tile[pid]
        if self.s.ownedby[t] != -1:
            raise RuntimeError("tile not declinable now")
        self._add_event("buy_declined", pid=pid, tile=t, doAuction=self.cfg.doAuction)

    def _resolve_unownable(self, pid: int, distance: int) -> None:
        t = self.s.tile[pid]
        if t == 0:
            return
        if t == 10:
            self._add_event("jail_visiting", pid=pid)
            return
        if t == 20:
            v = self.cfg.freeParkingValue
            if v is None:
                return
            if v == "tax":
                amt = self.s.freeparkingsum
                self.s.bal[pid] += amt
                self._add_event("free_parking", pid=pid, amount=amt, balance=self.s.bal[pid], mode="tax_pool")
                self.s.freeparkingsum = 0
                return
            if isinstance(v, int):
                self.s.bal[pid] += v
                self._add_event("free_parking", pid=pid, amount=v, balance=self.s.bal[pid], mode="fixed")
                return
            return
        if t == 30:
            self.s.injail[pid] = True
            self.s.tile[pid] = 10
            self.s.turn.was_doubles = False
            self._add_event("go_to_jail", pid=pid, reason="tile_30")
            return
        if t in (2, 17, 33):
            self._community_chest(pid)
            return
        if t in (7, 22, 36):
            self._chance(pid, distance)
            return
        if t == 4:
            self.s.bal[pid] -= self.cfg.incomeValue
            self.s.freeparkingsum += self.cfg.incomeValue
            self._add_event("tax", pid=pid, kind="income", amount=self.cfg.incomeValue, balance=self.s.bal[pid])
            return
        if t == 38:
            self.s.bal[pid] -= self.cfg.luxuryValue
            self.s.freeparkingsum += self.cfg.luxuryValue
            self._add_event("tax", pid=pid, kind="luxury", amount=self.cfg.luxuryValue, balance=self.s.bal[pid])
            return

    def _community_chest(self, pid: int) -> None:
        card = self.s.ccorder[self.s.ccn]
        self._add_event("card", pid=pid, deck="cc", card=card, text=(CCNAME[card] if card < len(CCNAME) else str(card)))
        if card == 0:
            self.s.tile[pid] = 0
            self._passed_go(pid, landed=True)
        elif card == 1:
            self.s.bal[pid] += 200
        elif card == 2:
            self.s.bal[pid] -= 50
            self.s.freeparkingsum += 50
        elif card == 3:
            self.s.bal[pid] += 50
        elif card == 4:
            self.s.goojf[pid] += 1
        elif card == 5:
            self.s.tile[pid] = 10
            self.s.injail[pid] = True
            self.s.turn.was_doubles = False
        elif card == 6:
            gain = 50 * (self.s.numalive - 1)
            self.s.bal[pid] += gain
            for i in range(self.s.num):
                if self.s.isalive[i] and i != pid:
                    self.s.bal[i] -= 50
                    self._add_event("transfer", from_pid=i, to_pid=pid, amount=50)
        elif card in (7, 10, 16):
            self.s.bal[pid] += 100
        elif card == 8:
            self.s.bal[pid] += 20
        elif card in (9, 15):
            self.s.bal[pid] += 10
        elif card == 11:
            self.s.bal[pid] -= 100
            self.s.freeparkingsum += 100
        elif card == 12:
            self.s.bal[pid] -= 150
            self.s.freeparkingsum += 150
        elif card == 13:
            self.s.bal[pid] += 25
        elif card == 14:
            pay = 0
            for i in range(40):
                if self.s.ownedby[i] == pid:
                    nh = self.s.numhouse[i]
                    if nh in (0, -1):
                        continue
                    if nh == 5:
                        pay += 115
                    else:
                        pay += 40 * nh
            self.s.bal[pid] -= pay
            self._add_event("repairs", pid=pid, amount=pay, deck="cc")
        self._add_event("balance", pid=pid, balance=self.s.bal[pid])
        self.s.ccn += 1
        if self.s.ccn > 16:
            self.rng.shuffle(self.s.ccorder)
            self.s.ccn = 0

    def _chance(self, pid: int, distance: int) -> None:
        card = self.s.chanceorder[self.s.chancen]
        self._add_event("card", pid=pid, deck="chance", card=card, text=(CHANCENAME[card] if card < len(CHANCENAME) else str(card)))
        if card == 0:
            self.s.tile[pid] = 0
            self._passed_go(pid, landed=True)
        elif card == 1:
            if self.s.tile[pid] > 24:
                self._passed_go(pid, landed=False)
            self.s.tile[pid] = 24
            self.land(pid, 0)
        elif card == 2:
            if self.s.tile[pid] > 11:
                self._passed_go(pid, landed=False)
            self.s.tile[pid] = 11
            self.land(pid, 0)
        elif card == 3:
            if self.s.tile[pid] <= 12:
                self.s.tile[pid] = 12
            elif self.s.tile[pid] <= 28:
                self.s.tile[pid] = 28
            else:
                self._passed_go(pid, landed=False)
                self.s.tile[pid] = 12
            t = self.s.tile[pid]
            owner = self.s.ownedby[t]
            if owner != pid and owner >= 0 and self.s.ismortgaged[t] != 1:
                amt = distance * 10
                self.s.bal[pid] -= amt
                self.s.bal[owner] += amt
                self._add_event("util_card_rent", pid=pid, owner=owner, amount=amt, tile=t)
            else:
                self.land(pid, 0)
        elif card == 4:
            t = self.s.tile[pid]
            if t <= 5:
                self.s.tile[pid] = 5
            elif t <= 15:
                self.s.tile[pid] = 15
            elif t <= 25:
                self.s.tile[pid] = 25
            elif t <= 35:
                self.s.tile[pid] = 35
            else:
                self._passed_go(pid, landed=False)
                self.s.tile[pid] = 5
            rr = self.s.tile[pid]
            owner = self.s.ownedby[rr]
            if owner != pid and owner >= 0 and self.s.ismortgaged[rr] != 1:
                rr_count = 0
                for p in (5, 15, 25, 35):
                    if self.s.ownedby[p] == owner:
                        rr_count += 1
                amt = RRPRICE[rr_count] * 2
                self.s.bal[pid] -= amt
                self.s.bal[owner] += amt
                self._add_event("rr_card_rent", pid=pid, owner=owner, amount=amt, tile=rr)
            else:
                self.land(pid, 0)
        elif card == 5:
            self.s.bal[pid] += 50
        elif card == 6:
            self.s.goojf[pid] += 1
        elif card == 7:
            self.s.tile[pid] -= 3
            if self.s.tile[pid] < 0:
                self.s.tile[pid] += 40
            self.land(pid, 0)
        elif card == 8:
            self.s.tile[pid] = 10
            self.s.injail[pid] = True
            self.s.turn.was_doubles = False
        elif card == 9:
            pay = 0
            for i in range(40):
                if self.s.ownedby[i] == pid:
                    nh = self.s.numhouse[i]
                    if nh in (0, -1):
                        continue
                    if nh == 5:
                        pay += 100
                    else:
                        pay += 25 * nh
            self.s.bal[pid] -= pay
            self._add_event("repairs", pid=pid, amount=pay, deck="chance")
        elif card == 10:
            self.s.bal[pid] -= 15
            self.s.freeparkingsum += 15
        elif card == 11:
            if self.s.tile[pid] > 5:
                self._passed_go(pid, landed=False)
            self.s.tile[pid] = 5
            self.land(pid, 0)
        elif card == 12:
            self.s.tile[pid] = 39
            self.land(pid, 0)
        elif card == 13:
            pay = 50 * (self.s.numalive - 1)
            self.s.bal[pid] -= pay
            for i in range(self.s.num):
                if self.s.isalive[i] and i != pid:
                    self.s.bal[i] += 50
                    self._add_event("transfer", from_pid=pid, to_pid=i, amount=50)
        elif card == 14:
            self.s.bal[pid] += 150
        elif card == 15:
            self.s.bal[pid] += 100
        self._add_event("balance", pid=pid, balance=self.s.bal[pid])
        self.s.chancen += 1
        if self.s.chancen > 15:
            self.rng.shuffle(self.s.chanceorder)
            self.s.chancen = 0

    def _pay_rr_util(self, pid: int, owner: int, tile: int, distance: int) -> None:
        if tile in (12, 28):
            both = self.s.ownedby[12] == self.s.ownedby[28]
            mult = 10 if both else 4
            amt = distance * mult
            self.s.bal[pid] -= amt
            self.s.bal[owner] += amt
            self._add_event("rent", kind="utility", pid=pid, owner=owner, tile=tile, amount=amt, balance=self.s.bal[pid])
            return
        if tile in (5, 15, 25, 35):
            rr_count = 0
            for p in (5, 15, 25, 35):
                if self.s.ownedby[p] == owner:
                    rr_count += 1
            amt = RRPRICE[rr_count]
            self.s.bal[pid] -= amt
            self.s.bal[owner] += amt
            self._add_event("rent", kind="rr", pid=pid, owner=owner, tile=tile, amount=amt, balance=self.s.bal[pid])
            return

    def _pay_property_rent(self, pid: int, owner: int, tile: int) -> None:
        is_monopoly = False
        for group in PROPGROUPS.values():
            if tile in group:
                if all(self.s.ownedby[prop] == owner for prop in group):
                    is_monopoly = True
                break
        if is_monopoly and self.s.numhouse[tile] == 0:
            rent = 2 * RENTPRICE[tile * 6]
        else:
            rent = RENTPRICE[(tile * 6) + self.s.numhouse[tile]]
        self.s.bal[pid] -= rent
        self.s.bal[owner] += rent
        self._add_event("rent", kind="property", pid=pid, owner=owner, tile=tile, amount=rent, balance=self.s.bal[pid])

    def forfeit_current_player(self) -> None:
        pid = self.cur()
        for i in range(40):
            if self.s.ownedby[i] == pid:
                self.s.ownedby[i] = -1
                if self.s.numhouse[i] > 0:
                    self.s.numhouse[i] = 0
                if self.s.ismortgaged[i] > 0:
                    self.s.ismortgaged[i] = 0
        self.s.numalive -= 1
        self.s.isalive[pid] = False
        self.s.injail[pid] = False
        self._add_event("forfeit", pid=pid, remaining_alive=self.s.numalive)

    def end_turn(self) -> None:
        pid = self.cur()
        self._add_event("turn_end", pid=pid, balance=self.s.bal[pid])
        self.s.turn.rolled = None
        self.advance_to_next_player()

    def mortgage_tile(self, tile: int) -> None:
        pid = self.cur()
        if self.s.ownedby[tile] != pid:
            raise RuntimeError("not owner")
        if self.s.numhouse[tile] != -1:
            group = PROPGROUPS.get(PROPCOLORS[tile], [])
            if group and not all(self.s.numhouse[p] == 0 for p in group):
                raise RuntimeError("houses exist in group")
        if self.s.ismortgaged[tile] != 0:
            raise RuntimeError("already mortgaged")
        self.s.ismortgaged[tile] = 1
        self.s.bal[pid] += MORTGAGEPRICE[tile]
        self._add_event("mortgage", pid=pid, tile=tile, amount=MORTGAGEPRICE[tile], balance=self.s.bal[pid])

    def unmortgage_tile(self, tile: int) -> None:
        pid = self.cur()
        if self.s.ownedby[tile] != pid:
            raise RuntimeError("not owner")
        if self.s.ismortgaged[tile] != 1:
            raise RuntimeError("not mortgaged")
        cost = TENMORTGAGEPRICE[tile]
        if self.s.bal[pid] < cost:
            raise RuntimeError("cannot afford")
        self.s.ismortgaged[tile] = 0
        self.s.bal[pid] -= cost
        self._add_event("unmortgage", pid=pid, tile=tile, cost=cost, balance=self.s.bal[pid])


class MonopolyAI:
    def __init__(self, me: int, name: Optional[str] = None):
        self.display_name = name or "[AI]"
        self.mention = self.display_name
        self.me = me
        self.cache: List[Any] = []

    def _get_min_safe(self, s: MonopolyState, cfg: GameConfig) -> int:
        high = 0
        high = max(high, cfg.incomeValue)
        high = max(high, cfg.luxuryValue)

        store: Dict[int, int] = {}
        for p in (5, 15, 25, 35):
            if s.ownedby[p] not in (-1, self.me):
                store[s.ownedby[p]] = store.get(s.ownedby[p], 0) + 1
        if store:
            high = max(high, RRPRICE[max(store.values())])

        if s.ownedby[12] == s.ownedby[28] and s.ownedby[12] not in (-1, self.me):
            high = max(high, 120)
        elif s.ownedby[12] not in (-1, self.me) or s.ownedby[28] not in (-1, self.me):
            high = max(high, 48)

        for group in PROPGROUPS.values():
            monopoly = (
                all(s.ownedby[p] == s.ownedby[group[0]] for p in group)
                and s.ownedby[group[0]] not in (-1, self.me)
            )
            for prop in group:
                if s.ownedby[prop] in (-1, self.me):
                    continue
                if s.numhouse[prop] == 0 and monopoly:
                    high = max(high, 2 * RENTPRICE[prop * 6])
                else:
                    high = max(high, RENTPRICE[prop * 6 + s.numhouse[prop]])

        if high >= 2000:
            return 1000
        return int(high - (0.00025 * (high ** 2)))

    @staticmethod
    def _subset_sum(options: Dict[int, int], goal: int, allow_above: bool) -> Dict[int, int]:
        best: List[int] = []
        store: List[List[int]] = [[]]
        existing_sums: Set[int] = set()

        while store:
            new_store: List[List[int]] = []
            for x in store:
                for option in options:
                    if x.count(option) == options[option]:
                        continue
                    hold = x[:] + [option]
                    s_hold = sum(hold)
                    if s_hold in existing_sums:
                        continue
                    if s_hold == goal:
                        result: Dict[int, int] = {}
                        for i in hold:
                            result[i] = result.get(i, 0) + 1
                        return result
                    if allow_above:
                        if sum(best) > goal:
                            if s_hold > sum(best):
                                continue
                            if s_hold > goal:
                                best = hold
                        else:
                            if s_hold > sum(best):
                                best = hold
                            if s_hold < goal:
                                new_store.append(hold)
                    else:
                        if s_hold > goal:
                            continue
                        if s_hold > sum(best):
                            best = hold
                        new_store.append(hold)
                    existing_sums.add(s_hold)
            store = new_store

        result: Dict[int, int] = {}
        for i in best:
            result[i] = result.get(i, 0) + 1
        return result

    def _buy_houses(self, s: MonopolyState, safe: int, cfg: GameConfig) -> Union[bool, str]:
        max_spend = s.bal[self.me] - safe
        max_hotels = cfg.hotelLimit
        max_houses = cfg.houseLimit

        possible_colors = [
            all(s.ownedby[p] == self.me for p in group)
            and not any(s.ismortgaged[p] == 1 for p in group)
            for group in PROPGROUPS.values()
        ]
        if not any(possible_colors):
            return False

        house_costs: Dict[int, List[List[int]]] = {}
        to_subset_sum: Dict[int, int] = {}
        n = -1
        pg = list(PROPGROUPS.values())

        for idx, possible in enumerate(possible_colors):
            if not possible:
                continue
            n += 1
            per = HOUSEPRICE[pg[idx][0]]
            count = min(max_spend // per, (len(pg[idx]) * 5) - sum(s.numhouse[p] for p in pg[idx]))
            if per not in house_costs:
                if count == 0:
                    continue
                house_costs[per] = [[idx, n]]
                to_subset_sum[per] = count
            else:
                if count > to_subset_sum[per]:
                    house_costs[per] = [[idx, n]]
                    to_subset_sum[per] = count
                elif count == to_subset_sum[per]:
                    house_costs[per].append([idx, n])

        subset_sum = self._subset_sum(to_subset_sum, max_spend, False)
        result: List[Any] = []
        new_numhouse = s.numhouse[:]

        for hc in subset_sum:
            idx, n = random.choice(house_costs[hc])
            result.append(n)
            to_change: Dict[int, int] = {}
            for _ in range(subset_sum[hc]):
                current_houses = [s.numhouse[p] for p in pg[idx]]
                for x in to_change:
                    current_houses[x] = to_change[x]
                prop_id = current_houses.index(min(current_houses))
                if prop_id in to_change:
                    if to_change[prop_id] == 5:
                        break
                    to_change[prop_id] += 1
                else:
                    to_change[prop_id] = s.numhouse[pg[idx][prop_id]] + 1
                new_numhouse[pg[idx][prop_id]] = to_change[prop_id]
            for x in to_change:
                result.append(x)
                result.append(to_change[x])
            result.append("c")

        if max_houses != -1 and sum(x for x in new_numhouse if x in (1, 2, 3, 4)) > max_houses:
            return False
        if max_hotels != -1 and sum(1 for x in new_numhouse if x == 5) > max_hotels:
            return False
        if not result:
            return False
        result.append("d")
        self.cache = result
        return "house_ai"

    def _sell_houses(self, s: MonopolyState, safe: int) -> Union[bool, str]:
        goal = safe - s.bal[self.me]
        possible_colors = [
            all(s.ownedby[p] == self.me for p in group)
            and not any(s.ismortgaged[p] for p in group)
            for group in PROPGROUPS.values()
        ]
        if not any(possible_colors):
            return False

        house_costs: Dict[int, List[List[int]]] = {}
        to_subset_sum: Dict[int, int] = {}
        n = -1
        pg = list(PROPGROUPS.values())

        for idx, possible in enumerate(possible_colors):
            if not possible:
                continue
            n += 1
            per = HOUSEPRICE[pg[idx][0]] // 2
            count = sum(s.numhouse[p] for p in pg[idx])
            if per not in house_costs:
                if count == 0:
                    continue
                house_costs[per] = [[idx, n]]
                to_subset_sum[per] = count
            else:
                if count > to_subset_sum[per]:
                    house_costs[per] = [[idx, n]]
                    to_subset_sum[per] = count
                elif count == to_subset_sum[per]:
                    house_costs[per].append([idx, n])

        subset_sum = self._subset_sum(to_subset_sum, goal, True)
        result: List[Any] = []

        for hc in subset_sum:
            idx, n = random.choice(house_costs[hc])
            result.append(n)
            to_change: Dict[int, int] = {}
            for _ in range(subset_sum[hc]):
                current_houses = [s.numhouse[p] for p in pg[idx]]
                for x in to_change:
                    current_houses[x] = to_change[x]
                prop_id = current_houses.index(max(current_houses))
                if prop_id in to_change:
                    if to_change[prop_id] == 0:
                        break
                    to_change[prop_id] -= 1
                else:
                    to_change[prop_id] = s.numhouse[pg[idx][prop_id]] - 1
            for x in to_change:
                result.append(x)
                result.append(to_change[x])
            result.append("c")

        if not result:
            return False
        result.append("d")
        self.cache = result
        return "house_ai"

    def _unmortgage(self, s: MonopolyState, safe: int) -> Union[bool, str]:
        max_spend = s.bal[self.me] - safe
        mortgageable = [a for a in range(40) if s.ownedby[a] == self.me and s.numhouse[a] <= 0]
        if not mortgageable:
            return False
        mortgage_value: Dict[int, List[int]] = {}
        to_subset_sum: Dict[int, int] = {}
        for idx, prop in enumerate(mortgageable):
            if s.ismortgaged[prop] != 1:
                continue
            per = TENMORTGAGEPRICE[prop]
            mortgage_value.setdefault(per, []).append(prop)
            to_subset_sum[per] = to_subset_sum.get(per, 0) + 1
        subset_sum = self._subset_sum(to_subset_sum, max_spend, False)
        result: List[Any] = []
        for price in subset_sum:
            sample = random.sample(mortgage_value[price], subset_sum[price])
            result.extend(sample)
        if not result:
            return False
        result.append("d")
        self.cache = result
        return "mortgage_ai"

    def _mortgage(self, s: MonopolyState, safe: int) -> Union[bool, str]:
        goal = safe - s.bal[self.me]
        mortgageable = [a for a in range(40) if s.ownedby[a] == self.me and s.numhouse[a] <= 0]
        if not mortgageable:
            return False
        mortgage_value: Dict[int, List[int]] = {}
        to_subset_sum: Dict[int, int] = {}
        for prop in mortgageable:
            if s.ismortgaged[prop] != 0:
                continue
            per = MORTGAGEPRICE[prop]
            mortgage_value.setdefault(per, []).append(prop)
            to_subset_sum[per] = to_subset_sum.get(per, 0) + 1
        subset_sum = self._subset_sum(to_subset_sum, goal, True)
        result: List[Any] = []
        for price in subset_sum:
            sample = random.sample(mortgage_value[price], subset_sum[price])
            result.extend(sample)
        if not result:
            return False
        result.append("d")
        self.cache = result
        return "mortgage_ai"

    @staticmethod
    def _calc_prop_value(s: MonopolyState, ownedby: List[int], player: int) -> int:
        value = 0
        for prop in range(40):
            if ownedby[prop] == player:
                value += PRICEBUY[prop]
                if s.ismortgaged[prop]:
                    value -= TENMORTGAGEPRICE[prop]
        for group in PROPGROUPS.values():
            if all(ownedby[p] == player for p in group):
                value += 1000
        return value

    def choose_action(self, s: MonopolyState, cfg: GameConfig, choices: List[str]) -> str:
        if "roll" in choices:
            return "roll"
        safe = self._get_min_safe(s, cfg)
        if s.bal[self.me] > safe:
            u = self._unmortgage(s, safe)
            if u:
                return "mortgage_ai"
            h = self._buy_houses(s, safe, cfg)
            if h:
                return "house_ai"
        if s.bal[self.me] < 0:
            sh = self._sell_houses(s, 0)
            if sh:
                return "house_ai"
            m = self._mortgage(s, 0)
            if m:
                return "mortgage_ai"
        if "end" in choices:
            return "end"
        if "forfeit" in choices:
            return "forfeit"
        return choices[0]

    def choose_buy(self, s: MonopolyState, cfg: GameConfig, prop_id: int) -> bool:
        safe = self._get_min_safe(s, cfg)
        return (s.bal[self.me] - PRICEBUY[prop_id]) >= safe

    def grab_from_cache(self) -> Any:
        if not self.cache:
            return "d"
        return self.cache.pop(0)


class MonopolyDirector:
    def __init__(self, engine: MonopolyEngine, ai_map: Dict[int, MonopolyAI]):
        self.e = engine
        self.ai_map = ai_map

    def attach_default_ai(self) -> None:
        for i, slot in enumerate(self.e.s.uid):
            if slot.is_ai and i not in self.ai_map:
                self.ai_map[i] = MonopolyAI(me=i, name=slot.ai_name)

    def step_auto_until_choice(self) -> List[EngineEvent]:
        self.e.clear_events()
        self.e.start_turn_events()
        self.attach_default_ai()

        while not self.e.game_over():
            pid = self.e.cur()
            if not self.e.s.isalive[pid]:
                self.e.advance_to_next_player()
                self.e.start_turn_events()
                continue

            if self.e.s.bal[pid] < 0:
                ai = self.ai_map.get(pid)
                if not ai:
                    break
                choice = ai.choose_action(self.e.s, self.e.cfg, self.e.legal_actions())
                if choice == "forfeit":
                    self.e.forfeit_current_player()
                    self.e.end_turn()
                    self.e.start_turn_events()
                    continue
                if choice == "mortgage_ai":
                    while True:
                        x = ai.grab_from_cache()
                        if x == "d":
                            break
                        self.e.mortgage_tile(int(x))
                    continue
                if choice == "house_ai":
                    while True:
                        x = ai.grab_from_cache()
                        if x == "d":
                            break
                        if x == "c":
                            continue
                    continue
                break

            acts = self.e.legal_actions()
            if not self.e.s.uid[pid].is_ai:
                break

            ai = self.ai_map.get(pid)
            if not ai:
                break

            choice = ai.choose_action(self.e.s, self.e.cfg, acts)

            if choice == "roll":
                if self.e.s.injail[pid]:
                    self.e.jail_roll()
                    if any(ev.kind == "jail_forced_bail" for ev in self.e.events):
                        self.e.pay_bail_and_roll()
                else:
                    self.e.normal_roll()
                t = self.e.s.tile[pid]
                if self.e.s.ownedby[t] == -1:
                    if ai.choose_buy(self.e.s, self.e.cfg, t):
                        self.e.buy_current_tile()
                    else:
                        self.e.decline_buy_current_tile()
                continue

            if choice == "end":
                self.e.end_turn()
                self.e.start_turn_events()
                continue

            if choice == "mortgage_ai":
                while True:
                    x = ai.grab_from_cache()
                    if x == "d":
                        break
                    tile = int(x)
                    if self.e.s.ismortgaged[tile] == 1:
                        try:
                            self.e.unmortgage_tile(tile)
                        except Exception:
                            pass
                    else:
                        try:
                            self.e.mortgage_tile(tile)
                        except Exception:
                            pass
                continue

            if choice == "house_ai":
                while True:
                    x = ai.grab_from_cache()
                    if x == "d":
                        break
                    if x == "c":
                        continue
                continue

            if choice == "forfeit":
                self.e.forfeit_current_player()
                self.e.end_turn()
                self.e.start_turn_events()
                continue

            break

        if self.e.game_over():
            w = self.e.winner()
            if w is not None:
                self.e._add_event("game_over", winner=w)
        return self.e.events
import discord
from discord.ext import commands
from discord import app_commands

class MonopolyRenderer:
    @staticmethod
    def state_text(s: MonopolyState) -> str:
        lines = []
        for i, slot in enumerate(s.uid):
            if not s.isalive[i]:
                continue
            name = slot.ai_name if slot.is_ai else f"<@{slot.user_id}>"
            jail = " 🟥" if s.injail[i] else ""
            lines.append(f"{name}: ${s.bal[i]} | {TILENAME[s.tile[i]]}{jail}")
        return "\n".join(lines)

    @staticmethod
    def events_text(events: List[EngineEvent]) -> str:
        out = []
        for e in events:
            k = e.kind
            d = e.data
            if k == "turn_start":
                out.append(f"▶️ Turn start")
            elif k == "rolled":
                out.append(f"🎲 Rolled {d['d1']} + {d['d2']}")
            elif k == "moved":
                out.append(f"➡️ Moved to {TILENAME[d['to_tile']]}")
            elif k == "rent":
                out.append(f"💸 Paid ${d['amount']} rent")
            elif k == "bought":
                out.append(f"🏠 Bought {TILENAME[d['tile']]}")
            elif k == "go_to_jail":
                out.append("🚔 Sent to jail")
            elif k == "free_parking":
                out.append(f"🎁 Free Parking +${d['amount']}")
            elif k == "game_over":
                out.append("🏆 Game Over")
        return "\n".join(out[-6:])

    @staticmethod
    def embed(events: List[EngineEvent], s: MonopolyState) -> discord.Embed:
        e = discord.Embed(title="Monopoly", color=0x2ecc71)
        e.add_field(name="Players", value=MonopolyRenderer.state_text(s), inline=False)
        txt = MonopolyRenderer.events_text(events)
        if txt:
            e.add_field(name="Log", value=txt, inline=False)
        e.set_footer(text=f"Current turn: {s.p + 1}")
        return e


class MonopolyView(discord.ui.View):
    def __init__(self, engine: MonopolyEngine, db: MonopolyDB, channel_id: int, guild_id: int):
        super().__init__(timeout=None)
        self.e = engine
        self.db = db
        self.channel_id = channel_id
        self.guild_id = guild_id
        self.sync_buttons()

    def sync_buttons(self):
        self.clear_items()
        acts = self.e.legal_actions()
        if "roll" in acts:
            self.add_item(MonopolyButton("Roll", "roll"))
        if "bail" in acts:
            self.add_item(MonopolyButton("Pay Bail", "bail"))
        if "use_goojf" in acts:
            self.add_item(MonopolyButton("Use GOOJF", "goojf"))
        if "end" in acts:
            self.add_item(MonopolyButton("End Turn", "end"))
        if "forfeit" in acts:
            self.add_item(MonopolyButton("Forfeit", "forfeit"))

    async def refresh(self, interaction: discord.Interaction):
        self.sync_buttons()
        self.db.save_game(self.channel_id, self.guild_id, self.e.s)
    
        board = interaction.client.get_cog("MonopolyCog").renderer.render(self.e.s)
        file = discord.File(io.BytesIO(board), filename="board.png")
    
        await interaction.message.edit(
            embed=MonopolyRenderer.embed(self.e.events, self.e.s),
            attachments=[file],
            view=self
        )

class MonopolyButton(discord.ui.Button):
    def __init__(self, label: str, action: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        view: MonopolyView = self.view
        e = view.e
        pid = e.cur()
        slot = e.s.uid[pid]

        if not slot.is_ai and slot.user_id != interaction.user.id:
            await interaction.response.send_message("Not your turn.", ephemeral=True)
            return

        e.clear_events()

        if self.action == "roll":
            if e.s.injail[pid]:
                e.jail_roll()
                if any(ev.kind == "jail_forced_bail" for ev in e.events):
                    e.pay_bail_and_roll()
            else:
                e.normal_roll()
            t = e.s.tile[pid]
            if e.s.ownedby[t] == -1:
                if slot.is_ai:
                    e.buy_current_tile()
        elif self.action == "bail":
            e.pay_bail_and_roll()
        elif self.action == "goojf":
            e.use_goojf_and_roll()
        elif self.action == "end":
            e.end_turn()
        elif self.action == "forfeit":
            e.forfeit_current_player()
            e.end_turn()

        director = MonopolyDirector(e, {})
        director.step_auto_until_choice()

        await interaction.response.defer()
        await view.refresh(interaction)
from PIL import Image, ImageDraw, ImageFont
import hashlib
import io

BOARD_POSITIONS = [
    (600,600),(520,600),(460,600),(400,600),(340,600),(280,600),(220,600),(160,600),(100,600),(40,600),
    (40,520),(40,460),(40,400),(40,340),(40,280),(40,220),(40,160),(40,100),(40,40),
    (100,40),(160,40),(220,40),(280,40),(340,40),(400,40),(460,40),(520,40),(600,40),
    (600,100),(600,160),(600,220),(600,280),(600,340),(600,400),(600,460),(600,520)
]

TOKEN_COLORS = [
    (231,76,60),(52,152,219),(46,204,113),(241,196,15),
    (155,89,182),(230,126,34),(26,188,156),(149,165,166)
]

class MonopolyBoardRenderer:
    def __init__(self, board_path="monopoly_board.png"):
        self.base = Image.open(board_path).convert("RGBA")
        self.cache: Dict[str, bytes] = {}

    def render(self, state: MonopolyState) -> bytes:
        key = hashlib.md5(state.to_json().encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
    
        img = self.base.copy()
        draw = ImageDraw.Draw(img)
    
        w, h = img.size
        m = int(w * 0.065)
        s = (w - 2 * m) // 9
    
        positions = []
        positions.append((w - m, h - m))
        for i in range(1, 10):
            positions.append((w - m - i * s, h - m))
        for i in range(1, 10):
            positions.append((m, h - m - i * s))
        for i in range(1, 10):
            positions.append((m + i * s, m))
        for i in range(1, 9):
            positions.append((w - m, m + i * s))
    
        token_size = int(w * 0.03)
        outline = max(2, token_size // 8)
    
        for i, alive in enumerate(state.isalive):
            if not alive:
                continue
    
            x, y = positions[state.tile[i]]
    
            ox = (i % 3) * (token_size + 4)
            oy = (i // 3) * (token_size + 4)
    
            cx = int(x + ox - token_size // 2)
            cy = int(y + oy - token_size // 2)
    
            draw.ellipse(
                (cx - outline, cy - outline, cx + token_size + outline, cy + token_size + outline),
                fill=(255, 255, 255, 255)
            )
    
            draw.ellipse(
                (cx, cy, cx + token_size, cy + token_size),
                fill=TOKEN_COLORS[i]
            )
    
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        self.cache[key] = buf.getvalue()
        return self.cache[key]


class MonopolyTradeView(discord.ui.View):
    def __init__(self, proposer: int, target: int, amount: int, engine: MonopolyEngine):
        super().__init__(timeout=60)
        self.proposer = proposer
        self.target = target
        self.amount = amount
        self.e = engine

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.e.s.uid[self.target].user_id:
            return
        self.e.s.bal[self.target] -= self.amount
        self.e.s.bal[self.proposer] += self.amount
        self.stop()
        await interaction.response.edit_message(content="Trade accepted", view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.e.s.uid[self.target].user_id:
            return
        self.stop()
        await interaction.response.edit_message(content="Trade declined", view=None)


class MonopolyAuctionView(discord.ui.View):
    def __init__(self, tile: int, engine: MonopolyEngine):
        super().__init__(timeout=60)
        self.tile = tile
        self.e = engine
        self.highest = 0
        self.bidder: Optional[int] = None

    @discord.ui.button(label="Bid +10", style=discord.ButtonStyle.primary)
    async def bid(self, interaction: discord.Interaction, _):
        for i, p in enumerate(self.e.s.uid):
            if not p.is_ai and p.user_id == interaction.user.id:
                if self.e.s.bal[i] >= self.highest + 10:
                    self.highest += 10
                    self.bidder = i
        await interaction.response.defer()

    @discord.ui.button(label="End Auction", style=discord.ButtonStyle.secondary)
    async def end(self, interaction: discord.Interaction, _):
        if self.bidder is not None:
            self.e.s.bal[self.bidder] -= self.highest
            self.e.s.ownedby[self.tile] = self.bidder
        self.stop()
        await interaction.response.edit_message(content="Auction ended", view=None)


class MonopolyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = MonopolyDB("data/monopoly.db")
        self.renderer = MonopolyBoardRenderer()
        self.games: Dict[int, MonopolyEngine] = {}
    @app_commands.command(
        name="monopoly_start",
        description="Start a new Monopoly game in this channel"
    )
    @app_commands.describe(
        opponent="Optional human opponent (otherwise you play against AI)"
    )
    async def monopoly_start(
        self,
        interaction: discord.Interaction,
        opponent: Optional[discord.Member] = None
    ):
        await interaction.response.defer()
    
        players = [PlayerSlot(interaction.user.id)]
        if opponent:
            players.append(PlayerSlot(opponent.id))
        else:
            players.append(PlayerSlot(0, is_ai=True))
    
        engine = MonopolyEngine.new_game(players, GameConfig())
        self.games[interaction.channel.id] = engine
    
        view = MonopolyView(engine, self.db, interaction.channel.id, interaction.guild.id)
        board = self.renderer.render(engine.s)
        file = discord.File(io.BytesIO(board), filename="board.png")
    
        await interaction.followup.send(
            embed=MonopolyRenderer.embed([], engine.s),
            view=view,
            file=file
        )
    
    
    @app_commands.command(
        name="monopoly_resume",
        description="Resume the saved Monopoly game in this channel"
    )
    async def monopoly_resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
    
        row = self.db.load_game(interaction.channel.id)
        if not row:
            await interaction.followup.send("No saved Monopoly game in this channel", ephemeral=True)
            return
    
        _, state = row
        engine = MonopolyEngine(state, GameConfig())
        self.games[interaction.channel.id] = engine
    
        view = MonopolyView(engine, self.db, interaction.channel.id, interaction.guild.id)
        board = self.renderer.render(engine.s)
        file = discord.File(io.BytesIO(board), filename="board.png")
    
        await interaction.followup.send(
            embed=MonopolyRenderer.embed([], engine.s),
            view=view,
            file=file,
            ephemeral=False
    )

    @app_commands.command(name="monopoly_stop", description="Stop the ongoing Monopoly game")
    async def monopoly_stop(self, interaction: discord.Interaction):
        self.db.delete_game(interaction.channel.id)
        self.games.pop(interaction.channel.id, None)
        await interaction.response.send_message("Game stopped")


async def setup(bot: commands.Bot):
    await bot.add_cog(MonopolyCog(bot))
