import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import asyncio, sqlite3, json, os, random, math, time
from dataclasses import dataclass
COLS = list("ABCDEFGHIJ") 
ROWS = list("0123456789")
GRID=10
LETTERS="ABCDEFGHIJ"
SHIP_SIZES=[5,4,3,3,2]

WATER="~"
MISS="o"
HIT="X"
SHIP="#"
SUNK_CELL="*"
BANNER="🧩"
HIT_EMOJI="🔥"
MISS_EMOJI="💦"
SUNK_EMOJI="💀"


DB_PATH=os.path.join("data","battleship.db")

def _idx(x,y): return y*10+x
def _xy(i): return i%10,i//10
def _inb(x,y): return 0<=x<10 and 0<=y<10
def _now(): return int(time.time())

def _ensure_db():
    os.makedirs("data",exist_ok=True)
    con=sqlite3.connect(DB_PATH)
    cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS games (channel_id INTEGER PRIMARY KEY, guild_id INTEGER, state_json TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS stats (user_id INTEGER PRIMARY KEY, wins INTEGER NOT NULL DEFAULT 0, losses INTEGER NOT NULL DEFAULT 0, elo REAL NOT NULL DEFAULT 1000)")
    cur.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER, channel_id INTEGER, p1_id INTEGER, p2_id INTEGER, winner_id INTEGER, ts INTEGER)")
    con.commit()
    con.close()

def _db(query, params=(), fetch=False, one=False):
    con=sqlite3.connect(DB_PATH)
    cur=con.cursor()
    cur.execute(query, params)
    out=None
    if fetch:
        out=cur.fetchone() if one else cur.fetchall()
    con.commit()
    con.close()
    return out

def _expected(ra, rb): 
    return 1.0/(1.0+10**((rb-ra)/400.0))

def _elo_update(r, opp, score, k=32):
    return r + k*(score - _expected(r, opp))

@dataclass
class Slot:
    user_id:int
    is_ai:bool=False
    ai_diff:str="normal"

class Board:
    def __init__(self, grid=None, ships=None, sunk=None):
        self.grid=grid[:] if grid else [0]*100
        self.ships=[s[:] for s in ships] if ships else []
        self.sunk=sunk[:] if sunk else [False]*len(self.ships)
    def render(self, reveal=False):
        out = []
        out.append("   " + " ".join(COLS))
    
        for y in range(GRID):
            row = [f"{ROWS[y]} "]
            for x in range(GRID):
                v = self.grid[_idx(x, y)]
                if v == 0:
                    cell = WATER
                elif v == 1:
                    cell = MISS
                elif v == 2:
                    cell = HIT
                elif v == 3 and reveal:
                    cell = SHIP
                else:
                    cell = WATER
                row.append(cell)
            out.append(" ".join(row))
    
        return "```" + "\n".join(out) + "```"

    def public_grid(self):
        return [0 if v==3 else v for v in self.grid]

    def can_place(self, x, y, d, length):
        if d=="r" and x+length>10: return False
        if d=="d" and y+length>10: return False
        for i in range(length):
            c=_idx(x+i,y) if d=="r" else _idx(x,y+i)
            if self.grid[c]!=0: return False
        return True

    def place(self, x, y, d, length):
        if not self.can_place(x,y,d,length): return False
        cells=[]
        for i in range(length):
            c=_idx(x+i,y) if d=="r" else _idx(x,y+i)
            self.grid[c]=3
            cells.append(c)
        self.ships.append(cells)
        self.sunk.append(False)
        return True

    def apply_shot(self, x, y):
        i=_idx(x,y)
        v=self.grid[i]
        if v in (1,2): return "repeat", None
        if v==0:
            self.grid[i]=1
            return "miss", None
        if v==3:
            self.grid[i]=2
            sunk_len=None
            for si,ship in enumerate(self.ships):
                if self.sunk[si]: 
                    continue
                if i in ship and all(self.grid[c]==2 for c in ship):
                    self.sunk[si]=True
                    sunk_len=len(ship)
            return "hit", sunk_len
        self.grid[i]=1
        return "miss", None

    def all_destroyed(self):
        return 3 not in self.grid

class SmartAI:
    def __init__(self, diff="normal"):
        self.diff=diff
        self.display_name=f"[AI:{diff}]"
        self.mention=self.display_name
        self.id=None

    async def send(self, *args, **kwargs):
        return

    def place_ship(self, board:Board, length:int):
        opts=[]
        for y in range(10):
            for x in range(10):
                for d in ("r","d"):
                    if board.can_place(x,y,d,length):
                        opts.append((x,y,d))
        if not opts: 
            return None
        if self.diff=="easy":
            return random.choice(opts)
        if self.diff in ("hard","god"):
            best=[]
            best_score=-1
            for x,y,d in opts:
                score=0
                for i in range(length):
                    cx,cy=(x+i,y) if d=="r" else (x,y+i)
                    if (cx+cy)%2==0: score+=1
                    if cx in (0,9): score+=0.2
                    if cy in (0,9): score+=0.2
                if score>best_score:
                    best_score=score
                    best=[(x,y,d)]
                elif score==best_score:
                    best.append((x,y,d))
            return random.choice(best)
        return random.choice(opts)

    def shoot(self, enemy_public, remaining_sizes):
        if self.diff=="easy":
            u=[i for i,v in enumerate(enemy_public) if v==0]
            if not u: return None
            i=random.choice(u)
            return _xy(i)

        hits=[i for i,v in enumerate(enemy_public) if v==2]
        def neigh(i):
            x,y=_xy(i)
            out=[]
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny=x+dx,y+dy
                if _inb(nx,ny): out.append(_idx(nx,ny))
            return out

        if hits:
            oriented=[]
            xs=[_xy(h)[0] for h in hits]
            ys=[_xy(h)[1] for h in hits]
            if len(hits)>=2:
                if len(set(xs))==1:
                    x=xs[0]
                    for y in (min(ys)-1, max(ys)+1):
                        if _inb(x,y):
                            j=_idx(x,y)
                            if enemy_public[j]==0: oriented.append(j)
                if len(set(ys))==1:
                    y=ys[0]
                    for x in (min(xs)-1, max(xs)+1):
                        if _inb(x,y):
                            j=_idx(x,y)
                            if enemy_public[j]==0: oriented.append(j)
            if oriented:
                j=random.choice(oriented) if self.diff=="normal" else max(oriented, key=lambda c: sum(enemy_public[n]==2 for n in neigh(c)))
                return _xy(j)

            cand=[]
            for h in hits:
                for n in neigh(h):
                    if enemy_public[n]==0:
                        cand.append(n)
            if cand:
                if self.diff=="normal":
                    j=random.choice(cand)
                else:
                    j=max(cand, key=lambda c: sum(enemy_public[n]==2 for n in neigh(c))*3 + sum(enemy_public[n]==0 for n in neigh(c)))
                return _xy(j)

        if self.diff!="god":
            u=[i for i,v in enumerate(enemy_public) if v==0 and ((i%10 + i//10)%2==0)]
            if not u:
                u=[i for i,v in enumerate(enemy_public) if v==0]
            if not u: return None
            scored=[]
            for i in u:
                x,y=_xy(i)
                s=0
                if (x+y)%2==0: s+=2
                for n in (i-1,i+1,i-10,i+10):
                    if 0<=n<100 and enemy_public[n]==0: s+=0.15
                scored.append((s,i))
            scored.sort(reverse=True)
            top=scored[:max(10,len(scored)//6)]
            j=random.choice([i for _,i in top])
            return _xy(j)

        u=[i for i,v in enumerate(enemy_public) if v==0]
        if not u: return None
        heat={i:0 for i in u}
        for length in remaining_sizes:
            for y in range(10):
                for x in range(10):
                    if x+length<=10:
                        cells=[_idx(x+k,y) for k in range(length)]
                        if all(enemy_public[c]==0 for c in cells):
                            for c in cells:
                                if c in heat: heat[c]+=1
                    if y+length<=10:
                        cells=[_idx(x,y+k) for k in range(length)]
                        if all(enemy_public[c]==0 for c in cells):
                            for c in cells:
                                if c in heat: heat[c]+=1
        j=max(heat, key=heat.get)
        return _xy(j)

class SpectatePanel(View):
    def __init__(self, cog, channel_id:int):
        super().__init__(timeout=900)
        self.cog=cog
        self.channel_id=channel_id

    @discord.ui.button(label="👀 Watch", style=discord.ButtonStyle.secondary, row=0)
    async def watch(self, interaction:discord.Interaction, _):
        g=self.cog.games.get(self.channel_id)
        if not g or not g.active:
            await interaction.response.send_message("No active game here.", ephemeral=True)
            return
        g.watch_messages.add((interaction.channel.id, interaction.message.id))
        await g.save()
        await interaction.response.send_message("This panel will update each turn.", ephemeral=True)

    @discord.ui.button(label="🛑 Stop", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction:discord.Interaction, _):
        g=self.cog.games.get(self.channel_id)
        if g:
            g.watch_messages.discard((interaction.channel.id, interaction.message.id))
            await g.save()
        await interaction.response.send_message("Stopped updating this panel.", ephemeral=True)

class DifficultySelectView(View):
    def __init__(self, owner_id:int):
        super().__init__(timeout=60)
        self.owner_id=owner_id
        self.choice=None
        self.done=asyncio.Event()
        self.add_item(DifficultySelect())

    async def interaction_check(self, interaction):
        if interaction.user.id!=self.owner_id:
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return False
        return True

class DifficultySelect(Select):
    def __init__(self):
        super().__init__(
            placeholder="Select AI difficulty",
            min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="Easy", value="easy", description="Chill, forgiving"),
                discord.SelectOption(label="Normal", value="normal", description="Smart hunt + target"),
                discord.SelectOption(label="Hard", value="hard", description="Aggressive finisher"),
                discord.SelectOption(label="Godlike", value="god", description="Probability heatmap"),
            ],
        )
    async def callback(self, interaction:discord.Interaction):
        v:DifficultySelectView=self.view
        v.choice=self.values[0]
        v.done.set()
        v.stop()
        await interaction.response.edit_message(content=f"AI difficulty: **{v.choice}**", view=None)
class SetupOrBattleView(View):
    def __init__(self, game, owner_id: int, mode: str):
        super().__init__(timeout=300)
        self.game = game
        self.owner_id = owner_id
        self.mode = mode
        self.sel_x = 0
        self.sel_y = 0
        self.dir = "r"

        for i in range(10):
            b = Button(
                label=str(i),
                style=discord.ButtonStyle.secondary,
                row=0 if i < 5 else 1,
                custom_id=f"r{i}",
            )
            b.callback = self.interaction_handler
            self.add_item(b)

        for i, c in enumerate(LETTERS):
            b = Button(
                label=c,
                style=discord.ButtonStyle.secondary,
                row=2 if i < 5 else 3,
                custom_id=f"c{i}",
            )
            b.callback = self.interaction_handler
            self.add_item(b)

        if mode == "setup":
            for cid, label, style in [
                ("rot", "🔄 Rotate", discord.ButtonStyle.primary),
                ("place", "✅ Place", discord.ButtonStyle.success),
                ("ff", "🏳️ Forfeit", discord.ButtonStyle.danger),
            ]:
                b = Button(label=label, style=style, row=4, custom_id=cid)
                b.callback = self.interaction_handler
                self.add_item(b)

        else:
            for cid, label, style in [
                ("fire", "🔥 FIRE", discord.ButtonStyle.danger),
                ("ff", "🏳️ Forfeit", discord.ButtonStyle.danger),
            ]:
                b = Button(label=label, style=style, row=4, custom_id=cid)
                b.callback = self.interaction_handler
                self.add_item(b)

    async def interaction_handler(self, interaction: discord.Interaction):
        cid = interaction.data["custom_id"]
    
        if cid == "rot":
            self.dir = "d" if self.dir == "r" else "r"
            await interaction.response.edit_message(
                content=self.game.screen_text(self.owner_id, self.mode, self.sel_x, self.sel_y, self.dir),
                view=self
            )
            return
    
        if cid == "ff":
            await interaction.response.edit_message(content="🏳️ Forfeit confirmed.", view=None)
            await self.game.forfeit(self.owner_id)
            self.stop()
            return
    
        if cid == "place":
            await self.game.place_ship(interaction, self.sel_x, self.sel_y, self.dir, self)
            return
    
        if cid == "fire":
            await self.game.fire(interaction, self.sel_x, self.sel_y, self)
            return
    
        if cid.startswith("r") and cid[1:].isdigit():
            self.sel_y = int(cid[1:])
            await interaction.response.edit_message(
                content=self.game.screen_text(self.owner_id, self.mode, self.sel_x, self.sel_y, self.dir),
                view=self
            )
            return
    
        if cid.startswith("c") and cid[1:].isdigit():
            self.sel_x = int(cid[1:])
            await interaction.response.edit_message(
                content=self.game.screen_text(self.owner_id, self.mode, self.sel_x, self.sel_y, self.dir),
                view=self
            )
            return

    
    async def interaction_check(self, interaction):
        if interaction.user.id!=self.owner_id:
            await interaction.response.send_message("Not for you.", ephemeral=True)
            return False
        if not self.game.active:
            await interaction.response.send_message("Game is over.", ephemeral=True)
            return False
        return True

class RematchView(View):
    def __init__(self, cog, channel_id:int, p1:int, p2:int, ai_diff:str|None):
        super().__init__(timeout=120)
        self.cog=cog
        self.channel_id=channel_id
        self.p1=p1
        self.p2=p2
        self.ai_diff=ai_diff

    @discord.ui.button(label="🔁 Rematch", style=discord.ButtonStyle.success, row=0)
    async def rematch(self, interaction:discord.Interaction, _):
        if interaction.user.id not in (self.p1, self.p2):
            await interaction.response.send_message("Not your match.", ephemeral=True)
            return
        await interaction.response.send_message("Starting rematch…", ephemeral=True)
        await self.cog.start_match(interaction.channel, self.p1, self.p2, ai_diff=self.ai_diff, force=True)

class BattleshipGame:
    def __init__(self, cog, channel, guild_id:int, slots:list[Slot]):
        self.cog=cog
        self.bot=cog.bot
        self.channel=channel
        self.guild_id=guild_id
        self.slots=slots
        self.boards=[Board(), Board()]
        self.turn=0
        self.phase="setup"
        self.active=True
        self.setup_progress=[0,0]
        self.screen_msg_id=None
        self.watch_messages=set()
        self.ai=None
        if any(s.is_ai for s in slots):
            diff=next(s.ai_diff for s in slots if s.is_ai)
            self.ai=SmartAI(diff)

    def state(self):
        return {
            "slots":[{"user_id":s.user_id,"is_ai":s.is_ai,"ai_diff":s.ai_diff} for s in self.slots],
            "boards":[{"grid":b.grid,"ships":b.ships,"sunk":b.sunk} for b in self.boards],
            "turn":self.turn,
            "phase":self.phase,
            "active":self.active,
            "setup_progress":self.setup_progress,
            "screen_msg_id":self.screen_msg_id,
            "watch_messages":[list(x) for x in self.watch_messages],
        }

    @classmethod
    def from_state(cls, cog, channel, guild_id:int, state):
        slots=[Slot(**d) for d in state["slots"]]
        g=cls(cog, channel, guild_id, slots)
        g.boards=[Board(**state["boards"][0]), Board(**state["boards"][1])]
        g.turn=state["turn"]
        g.phase=state["phase"]
        g.active=state["active"]
        g.setup_progress=state.get("setup_progress",[0,0])
        g.screen_msg_id=state.get("screen_msg_id")
        g.watch_messages=set(tuple(x) for x in state.get("watch_messages",[]))
        if any(s.is_ai for s in slots):
            diff=next(s.ai_diff for s in slots if s.is_ai)
            g.ai=SmartAI(diff)
        return g

    async def save(self):
        cid=getattr(self.channel,"id",None)
        if cid is None: return
        _db("INSERT INTO games(channel_id,guild_id,state_json) VALUES(?,?,?) ON CONFLICT(channel_id) DO UPDATE SET guild_id=excluded.guild_id,state_json=excluded.state_json",
            (cid, self.guild_id, json.dumps(self.state())))
    async def delete_save(self):
        cid=getattr(self.channel,"id",None)
        if cid is None: return
        _db("DELETE FROM games WHERE channel_id=?", (cid,))

    def slot_index(self, user_id:int):
        for i,s in enumerate(self.slots):
            if (not s.is_ai) and s.user_id==user_id:
                return i
        return None

    async def resolve(self, slot:Slot):
        if slot.is_ai: return self.ai
        u=self.bot.get_user(slot.user_id)
        if u: return u
        return await self.bot.fetch_user(slot.user_id)

    def remaining_enemy_sizes(self):
        b=self.boards[1-self.turn]
        sizes=[]
        for ship, sunk in zip(b.ships, b.sunk):
            if not sunk:
                sizes.append(len(ship))
        return sizes if sizes else SHIP_SIZES[:]

    def banner(self, title:str):
        return f"{BANNER} **{title}**\n"

    def screen_text(self, viewer_id:int, mode:str, x:int, y:int, d:str):
        v_idx=self.slot_index(viewer_id)
        arrow="➡️" if d=="r" else "⬇️"
        if mode=="setup":
            b=self.boards[v_idx]
            l=SHIP_SIZES[self.setup_progress[v_idx]]
            ok="✅" if b.can_place(x,y,d,l) else "❌"
            hdr=self.banner("SHIPYARD")
            return hdr + f"Place ship **{l}**  |  Start **{LETTERS[x]}{y}** {arrow}  |  Valid {ok}\n\n" + b.render(reveal=True)
        enemy=self.boards[1-self.turn]
        hdr=self.banner("BATTLEFIELD")
        return hdr + f"Target **{LETTERS[x]}{y}**\n\n" + enemy.render(reveal=False)

    async def ensure_screen(self):
        if self.screen_msg_id:
            try:
                m=await self.channel.fetch_message(self.screen_msg_id)
                return m
            except Exception:
                self.screen_msg_id=None
        m=await self.channel.send(self.banner("LOADING") + "Initializing…")
        self.screen_msg_id=m.id
        await self.save()
        return m

    async def push_watch_updates(self, content:str):
        dead=set()
        for ch_id, msg_id in list(self.watch_messages):
            try:
                ch=self.bot.get_channel(ch_id) or await self.bot.fetch_channel(ch_id)
                msg=await ch.fetch_message(msg_id)
                await msg.edit(content=content, view=SpectatePanel(self.cog, getattr(self.channel,"id",0)))
            except Exception:
                dead.add((ch_id,msg_id))
        if dead:
            self.watch_messages-=dead
            await self.save()

    async def start(self):
        await self.save()
        await self.run_setup_step()

    async def run_setup_step(self):
        if not self.active: return
        self.phase="setup"
        await self.save()
        m=await self.ensure_screen()

        for p in range(2):
            slot=self.slots[p]
            if slot.is_ai:
                while self.setup_progress[p]<len(SHIP_SIZES):
                    l=SHIP_SIZES[self.setup_progress[p]]
                    pos=self.ai.place_ship(self.boards[p], l)
                    if not pos:
                        await self.end(None, reason="AI failed placement")
                        return
                    x,y,d=pos
                    self.boards[p].place(x,y,d,l)
                    self.setup_progress[p]+=1
                    await self.save()
                continue

            if self.setup_progress[p]>=len(SHIP_SIZES):
                continue

            u=await self.resolve(slot)
            l=SHIP_SIZES[self.setup_progress[p]]
            view=SetupOrBattleView(self, u.id, "setup")
            txt=self.screen_text(u.id, "setup", 0, 0, "r")
            try:
                await u.send(txt, view=view)
            except discord.Forbidden:
                await self.end(None, reason=f"{u.display_name} has DMs closed")
                return

        if self.setup_progress[0]>=len(SHIP_SIZES) and self.setup_progress[1]>=len(SHIP_SIZES):
            self.phase="battle"
            self.turn=0
            await self.save()
            await self.run_battle_turn()
            return

        await m.edit(content=self.banner("SHIPYARD") + "Players are placing ships in DMs.\n\nWant to watch? Use the panel below.", view=SpectatePanel(self.cog, getattr(self.channel,"id",0)))
        await self.push_watch_updates(self.banner("SHIPYARD") + "Ship placement in progress…")

    async def place_ship(self, interaction:discord.Interaction, x:int, y:int, d:str, view:View):
        p=self.slot_index(interaction.user.id)
        if p is None:
            await interaction.response.send_message("Not your setup.", ephemeral=True)
            return
        if self.phase!="setup" or not self.active:
            await interaction.response.send_message("Setup is over.", ephemeral=True)
            return
        if self.setup_progress[p]>=len(SHIP_SIZES):
            await interaction.response.send_message("You already placed all ships.", ephemeral=True)
            return
        length=SHIP_SIZES[self.setup_progress[p]]
        b=self.boards[p]
        if not b.can_place(x,y,d,length):
            await interaction.response.send_message("Invalid placement.", ephemeral=True)
            return
        b.place(x,y,d,length)
        self.setup_progress[p]+=1
        await self.save()
        await interaction.response.edit_message(content=f"✅ Placed ship **{length}**.", view=None)

        if self.setup_progress[0]>=len(SHIP_SIZES) and self.setup_progress[1]>=len(SHIP_SIZES):
            self.phase="battle"
            self.turn=0
            await self.save()
            await self.run_battle_turn()
            return
        await self.run_setup_step()

    async def run_battle_turn(self):
        if not self.active: return
        if self.phase!="battle": return

        m=await self.ensure_screen()
        cur_slot=self.slots[self.turn]
        enemy_slot=self.slots[1-self.turn]

        if cur_slot.is_ai:
            await asyncio.sleep(1)
            enemy_pub=self.boards[1-self.turn].public_grid()
            sizes=self.remaining_enemy_sizes()
            shot=self.ai.shoot(enemy_pub, sizes)
            if not shot:
                await self.end(None, reason="AI cannot move")
                return
            x,y=shot
            await self._apply_fire(None, x,y, ai=True)
            return

        cur=await self.resolve(cur_slot)
        v=SetupOrBattleView(self, cur.id, "battle")
        txt=self.screen_text(cur.id, "battle", 0, 0, "r")
        await m.edit(content=self.banner("BATTLEFIELD")+f"🎯 Turn: **{cur.display_name}**\n\n"+self.boards[1-self.turn].render(False), view=v)
        await self.push_watch_updates(self.banner("BATTLEFIELD")+f"🎯 Turn: **{cur.display_name}**\n\n"+self.boards[1-self.turn].render(False))
        await self.save()

    async def fire(self, interaction:discord.Interaction, x:int, y:int, view:View):
        if self.phase!="battle" or not self.active:
            await interaction.response.send_message("Game is not in battle.", ephemeral=True)
            return
        if self.slot_index(interaction.user.id)!=self.turn:
            await interaction.response.send_message("Not your turn.", ephemeral=True)
            return
        await self._apply_fire(interaction, x,y, ai=False)

    async def _apply_fire(self, interaction, x:int, y:int, ai:bool):
        enemy=self.boards[1-self.turn]
        res, sunk_len = enemy.apply_shot(x,y)
        if res=="repeat":
            if interaction and hasattr(interaction,"response"):
                await interaction.response.send_message("Already fired there.", ephemeral=True)
            return

        who=self.ai.display_name if (ai and self.ai) else (interaction.user.display_name if interaction else "AI")
        cell=f"{LETTERS[x]}{y}"
        if res == "miss":
            msg = f"{MISS_EMOJI} **MISS** — {who} at **{cell}**"
            self.turn ^= 1
        else:
            msg = f"{HIT_EMOJI} **HIT** — {who} at **{cell}**"
            if sunk_len:
                msg += f"  {SUNK_EMOJI} **SUNK ship ({sunk_len})**"


        m=await self.ensure_screen()
        await m.edit(content=self.banner("BATTLEFIELD")+msg+"\n\n"+enemy.render(False), view=None)
        await self.push_watch_updates(self.banner("BATTLEFIELD")+msg+"\n\n"+enemy.render(False))

        if enemy.all_destroyed():
            winner_idx=self.turn if res=="hit" else (1-self.turn)
            await self.end(winner_idx, reason="victory")
            return

        await self.save()
        await self.run_battle_turn()

    async def forfeit(self, user_id:int):
        if not self.active: return
        p=self.slot_index(user_id)
        if p is None:
            return
        winner=1-p
        await self.end(winner, reason="forfeit")

    async def end(self, winner_idx:int|None, reason:str):
        if not self.active: return
        self.active=False
        await self.save()

        cid=getattr(self.channel,"id",0)
        p1_id=self.slots[0].user_id if not self.slots[0].is_ai else 0
        p2_id=self.slots[1].user_id if not self.slots[1].is_ai else 0
        ai_diff=self.slots[0].ai_diff if self.slots[0].is_ai else (self.slots[1].ai_diff if self.slots[1].is_ai else None)

        if winner_idx is None:
            text=self.banner("GAME OVER")+"Game ended."
        else:
            win_slot=self.slots[winner_idx]
            win_name=(self.ai.display_name if win_slot.is_ai else (await self.resolve(win_slot)).display_name)
            text=self.banner("GAME OVER")+f"🏆 **{win_name}** wins!"

        await self.push_watch_updates(text)
        try:
            m=await self.ensure_screen()
            await m.edit(content=text, view=RematchView(self.cog, cid, p1_id, p2_id, ai_diff))
        except Exception:
            await self.channel.send(text, view=RematchView(self.cog, cid, p1_id, p2_id, ai_diff))

        if winner_idx is not None and (not self.slots[0].is_ai) and (not self.slots[1].is_ai):
            w_id=self.slots[winner_idx].user_id
            l_id=self.slots[1-winner_idx].user_id
            _db("INSERT OR IGNORE INTO stats(user_id,wins,losses,elo) VALUES(?,?,?,?)",(w_id,0,0,1000))
            _db("INSERT OR IGNORE INTO stats(user_id,wins,losses,elo) VALUES(?,?,?,?)",(l_id,0,0,1000))
            w=_db("SELECT wins,losses,elo FROM stats WHERE user_id=?",(w_id,),fetch=True,one=True)
            l=_db("SELECT wins,losses,elo FROM stats WHERE user_id=?",(l_id,),fetch=True,one=True)
            w_elo=w[2]; l_elo=l[2]
            w_new=_elo_update(w_elo,l_elo,1.0)
            l_new=_elo_update(l_elo,w_elo,0.0)
            _db("UPDATE stats SET wins=wins+1, elo=? WHERE user_id=?",(w_new,w_id))
            _db("UPDATE stats SET losses=losses+1, elo=? WHERE user_id=?",(l_new,l_id))
            _db("INSERT INTO history(guild_id,channel_id,p1_id,p2_id,winner_id,ts) VALUES(?,?,?,?,?,?)",(self.guild_id, cid, p1_id, p2_id, w_id, _now()))

        await self.delete_save()
        self.cog.games.pop(getattr(self.channel,"id",0), None)

class BattleshipCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot=bot
        self.games={}

    async def cog_load(self):
        _ensure_db()

    async def start_match(self, channel, p1_id:int, p2_id:int, ai_diff:str|None=None, force:bool=False):
        cid=channel.id
        if cid in self.games and not force:
            await channel.send("A game is already running here.")
            return
        slots=[Slot(p1_id, False, "normal"), Slot(p2_id, False, "normal")]
        if p2_id==0:
            slots[1]=Slot(0, True, ai_diff or "normal")
        g=BattleshipGame(self, channel, getattr(channel.guild,"id",0), slots)
        self.games[cid]=g
        await g.save()
        await channel.send(BANNER+" **BATTLESHIP ONLINE**\nA full game screen will appear. Want to watch? Use the panel below.", view=SpectatePanel(self, cid))
        await g.start()

    @app_commands.command(name="battleship", description="Start Battleship (game-engine mode)")
    async def battleship(self, interaction:discord.Interaction, opponent:discord.Member|None=None):
        await interaction.response.defer(ephemeral=True)
        channel=interaction.channel
        if isinstance(channel, discord.TextChannel):
            try:
                channel=await channel.create_thread(name="Battleship")
            except Exception:
                channel=interaction.channel
        if opponent:
            await interaction.followup.send(f"Starting vs **{opponent.display_name}**…", ephemeral=True)
            await self.start_match(channel, interaction.user.id, opponent.id)
            return
        v=DifficultySelectView(interaction.user.id)
        await interaction.followup.send("Pick AI difficulty:", view=v, ephemeral=True)
        await v.done.wait()
        diff=v.choice or "normal"
        await self.start_match(channel, interaction.user.id, 0, ai_diff=diff)

    @app_commands.command(name="battleship_resume", description="Resume a saved game in this channel/thread")
    async def battleship_resume(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cid=interaction.channel.id
        if cid in self.games:
            await interaction.followup.send("A game is already active here.", ephemeral=True)
            return
        row=_db("SELECT guild_id,state_json FROM games WHERE channel_id=?",(cid,),fetch=True,one=True)
        if not row:
            await interaction.followup.send("No saved game found here.", ephemeral=True)
            return
        guild_id, state_json=row
        g=BattleshipGame.from_state(self, interaction.channel, guild_id, json.loads(state_json))
        self.games[cid]=g
        await interaction.followup.send("Game resumed.", ephemeral=True)
        if g.phase=="setup":
            await g.run_setup_step()
        else:
            await g.run_battle_turn()

    @app_commands.command(name="battleship_forfeit", description="Forfeit the current game in this channel/thread")
    async def battleship_forfeit(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        g=self.games.get(interaction.channel.id)
        if not g:
            await interaction.followup.send("No active game here.", ephemeral=True)
            return
        await interaction.followup.send("Forfeit sent.", ephemeral=True)
        await g.forfeit(interaction.user.id)

    @app_commands.command(name="battleship_stats", description="Show Battleship stats")
    async def battleship_stats(self, interaction:discord.Interaction, user:discord.User|None=None):
        await interaction.response.defer(ephemeral=True)
        user=user or interaction.user
        row=_db("SELECT wins,losses,elo FROM stats WHERE user_id=?",(user.id,),fetch=True,one=True)
        if not row:
            await interaction.followup.send(f"No stats for **{user.display_name}** yet.", ephemeral=True)
            return
        w,l,e=row
        await interaction.followup.send(f"📊 **{user.display_name}**\nWins: **{w}** | Losses: **{l}** | ELO: **{e:.0f}**", ephemeral=True)

    @app_commands.command(name="battleship_leaderboard", description="Top ELO leaderboard")
    async def battleship_leaderboard(self, interaction:discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rows=_db("SELECT user_id,wins,losses,elo FROM stats ORDER BY elo DESC LIMIT 10", fetch=True)
        if not rows:
            await interaction.followup.send("No leaderboard yet.", ephemeral=True)
            return
        lines=[]
        for n,(uid,w,l,e) in enumerate(rows, start=1):
            u=self.bot.get_user(uid)
            name=u.display_name if u else str(uid)
            lines.append(f"**{n}.** {name} — ELO **{e:.0f}**  (W{w}/L{l})")
        await interaction.followup.send("🏆 **Battleship Leaderboard**\n"+"\n".join(lines), ephemeral=True)

async def setup(bot:commands.Bot):
    await bot.add_cog(BattleshipCog(bot))
