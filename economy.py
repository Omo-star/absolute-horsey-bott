# beta owo-bot esque feature!

import discord
from discord.ext import commands
from discord import app_commands
import datetime
import asyncio
import random
import json, os
STOCKS = {
    "HRS":   {"name": "Horsey Corp",              "price": 120, "volatility": 0.05},
    "MOO":   {"name": "Moo Industries",           "price": 80,  "volatility": 0.04},
    "NAY":   {"name": "Neigh Technologies",       "price": 150, "volatility": 0.06},
    "UDDR":  {"name": "UdderBank",                "price": 95,  "volatility": 0.03},

    "HOOF":  {"name": "Hoof Logistics",           "price": 60,  "volatility": 0.07},
    "HAY":   {"name": "HayStack Farms",           "price": 45,  "volatility": 0.05},
    "WHNY":  {"name": "Whinny Media Group",       "price": 135, "volatility": 0.06},
    "TROT":  {"name": "Trot Motors",              "price": 200, "volatility": 0.08},

    "GALP":  {"name": "Gallop Aerospace",         "price": 260, "volatility": 0.09},
    "MINT":  {"name": "Minty Pasture Drinks",     "price": 55,  "volatility": 0.05},
    "CLVR":  {"name": "Clover Softworks",         "price": 110, "volatility": 0.045},
    "BEEF":  {"name": "BEEF Defense Systems",     "price": 165, "volatility": 0.07},

    "HNGR":  {"name": "Hungerhorse Foods",        "price": 70,  "volatility": 0.045},
    "SALT":  {"name": "Salt Lick Mining Co.",     "price": 90,  "volatility": 0.05},
    "GLUE":  {"name": "GlueTech Supplies",        "price": 30,  "volatility": 0.08},   
    "PRNC":  {"name": "Prance Entertainment",     "price": 180, "volatility": 0.065},

    "STBL":  {"name": "StableCoin Ltd.",          "price": 150, "volatility": 0.015},  
    "CART":  {"name": "CartWheel Robotics",       "price": 220, "volatility": 0.07},
    "MANE":  {"name": "Mane Fashion Group",       "price": 95,  "volatility": 0.055},
    "WHIP":  {"name": "WhipSpeed AI Systems",     "price": 300, "volatility": 0.09},
}

def simulate_stock_prices():

    global MARKET_SENTIMENT

    if "MARKET_SENTIMENT" not in globals():
        MARKET_SENTIMENT = 0.0
    MARKET_SENTIMENT *= 0.9
    MARKET_SENTIMENT += random.uniform(-0.03, 0.03)
    MARKET_SENTIMENT = max(min(MARKET_SENTIMENT, 1.0), -1.0)
    volatility_wave = random.uniform(0.85, 1.25)
    event = None
    event_multiplier = 1.0

    roll = random.random()
    if roll < 0.004:
        event = "💥 Global Market Crash"
        event_multiplier = random.uniform(0.60, 0.85)
        MARKET_SENTIMENT -= random.uniform(0.3, 0.6)

    elif roll < 0.008:
        event = "🚀 Market Euphoria Bubble"
        event_multiplier = random.uniform(1.10, 1.35)
        MARKET_SENTIMENT += random.uniform(0.3, 0.5)

    elif roll < 0.015:
        event = "📉 Interest Rate Scare"
        event_multiplier = random.uniform(0.90, 0.97)
        MARKET_SENTIMENT -= 0.2

    elif roll < 0.020:
        event = "📈 Positive Employment Report"
        event_multiplier = random.uniform(1.02, 1.08)
        MARKET_SENTIMENT += 0.15

    SECTORS = {
        "tech":   ["NAY", "CLVR", "WHIP"],
        "finance": ["UDDR", "STBL"],
        "media": ["WHNY", "PRNC"],
        "transport": ["HOOF", "TROT", "CART"],
        "food": ["HAY", "HNGR", "MINT"],
        "industry": ["BEEF", "SALT", "GLUE"],
        "luxury": ["MANE", "MOO"]
    }

    sector_sentiment = {s: MARKET_SENTIMENT + random.uniform(-0.1, 0.1) for s in SECTORS}

    individual_events = {} 

    for symbol in STOCKS:
        roll = random.random()

        if roll < 0.01:
            individual_events[symbol] = (1.20, "📈 Breakthrough Tech Release")
        elif roll < 0.02:
            individual_events[symbol] = (0.85, "📉 Supply Chain Issues")
        elif roll < 0.025:
            individual_events[symbol] = (1.40, "🚀 Insider Buy Surge")
        elif roll < 0.03:
            individual_events[symbol] = (0.75, "💀 Scandal")

    for symbol, data in STOCKS.items():

        price = data["price"]
        vol = data["volatility"]
        stock_sector = next(
            (name for name, syms in SECTORS.items() if symbol in syms),
            None
        )

        sec_sent = sector_sentiment.get(stock_sector, 0)
        momentum = data.get("momentum", 0.0)
        momentum *= 0.85
        momentum += random.uniform(-0.02, 0.02)
        reversion = (150 - price) / 1500  
        random_move = random.gauss(0, vol)
        move = (
            random_move +
            (MARKET_SENTIMENT * 0.15) +
            (sec_sent * 0.10) +
            (momentum * 0.25) +
            reversion
        )
        move *= event_multiplier
        if symbol in individual_events:
            m, _ = individual_events[symbol]
            move *= m
        new_price = int(price * (1 + move))
        new_price = max(new_price, 1)
        if new_price < price * 0.80:
            new_price = int(price * 0.80)
        data["momentum"] = momentum
        data["price"] = new_price
    return event, individual_events

STATE_FILE = "state.json"
def get_pray_boost(user_id: int):
    user = get_user(user_id)
    pray_points = user.get("pray", 0)

    boost = 1 + min(pray_points * 0.015, 0.20)
    return boost

def load_state():
    default = {
        "users": {},
        "items": {
            "intercontinental_ballistic_missile": {"name": "Intercontinental Ballistic Missile", "price": 1000},
            "red_button": {"name": "r̶̭̖͊̄̕é̶̖͝͝d̴̤̙̓̔̚ ̸̙̫̄̂͝ͅb̵̼͖͓͊̓͜ṵ̴̹̐͋t̴̳̘͖̎̊͘͝ț̴̨̰͒ò̵̗̠͊n̶͎̱̑͐̿ ̸̪̭̀̊̈́̓ơ̵̻̹̎̐f̶̠̗̭̻̓̎ ̵͔̣̖͓̐͋d̵̝̖͛̊͛e̸͉͚̹̺͐̍͘͘â̸̡̑̑͝t̴̛̝͍̊̀h̷̯͎̮̊", "price": 1500},
            "mysterious_potion": {"name": "Mysterious Potion", "price": 2000},
            "roast_protection": {"name": "Roast Protection Pill", "price": 5000},
            "odd_box": {"name": "Interesting Box", "price": 5000},
            "quantum_marshmallow": {"name": "Quantum Marshmallow", "price": 350},
            "time_bending_hourglass": {"name": "Time-Bending Hourglass", "price": 1200},
            "void_pebble": {"name": "Pebble From The Void", "price": 900},
            "cursed_duck": {"name": "C͝u͘r͟s̕e͢d̷ D̀u̸c͢k̡ ͠of̧ W͝h͞i̡sp̀ęr̴s", "price": 1600},
            "pocket_dimension_seed": {"name": "Pocket Dimension Seed", "price": 2400},
            "ethereal_lantern": {"name": "Ethereal Lantern", "price": 800},
            "glitched_coin": {"name": "G̵l̴i̶t̵c̷h̷e̷d̶ ̶C̵o̵i̶n̸", "price": 666},
            "orb_of_unlikely_events": {"name": "Orb of Unlikely Events", "price": 1100},
            "sentient_spoon": {"name": "Sentient Spoon", "price": 700},
            "chaos_sandwich": {"name": "C͢h̨a͡ǫs̷ ̨S͘a͘n̡d̷w̶i͡ćh", "price": 1300},
            "lurking_shadow_fragment": {"name": "Shadow Fragment", "price": 1850},
            "rainbow_thunder_crystal": {"name": "Rainbow Crystal", "price": 1500},
            "mechanical_gremlin": {"name": "Mechanical Gremlin", "price": 900},
            "antigravity_rubber_ducky": {"name": "Anti-Gravity Rubber Ducky", "price": 500},
            "forgotten_scroll": {"name": "Forgotten Scroll of Maybe-Magic", "price": 1400},
            "ancient_snack": {"name": "Ancient Snack of Eternity", "price": 300},
            "starlit_compass": {"name": "Compass of Starlit Paths", "price": 950},
            "cryptic_cube": {"name": "Cryptic Cube", "price": 1250},
            "cookie_unstable": {"name": "Cookie", "price": 550},
            "paradox_clock": {"name": "P͝a͜r̛a̢d͘o̢x̷ ͠C͠l̴o͠c̨k̀", "price": 2000}
        }
    }

    if not os.path.exists(STATE_FILE):
        return default

    with open(STATE_FILE, "r") as f:
        data = json.load(f)

    data["items"] = default["items"]

    return data


def save_state():
    global state
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

state = load_state()

def set_cooldown(user_id: int, key: str, hours: int):
    user = get_user(user_id)
    user[key] = (datetime.datetime.utcnow() + datetime.timedelta(hours=hours)).isoformat()
    save_state()

def get_cooldown(user_id: int, key: str):
    user = get_user(user_id)
    ts = user.get(key)
    if not ts:
        return None
    return datetime.datetime.fromisoformat(ts)

def get_user(uid: int):
    global state
    uid = str(uid)

    if uid not in state["users"]:
        state["users"][uid] = {
            "balance": 0,
            "last_daily": None,
            "last_work": None,
            "fish_cooldown": None,
            "hunt_cooldown": None,
            "inventory": {},
            "roast_protection_until": None,
            "pray": 0,
            "last_pray": None,
            "codepad": {},
            "owned_animals": [],
            "team": []
        }
        save_state()

    user = state["users"][uid]
    user.setdefault("pray", 0)
    user.setdefault("last_pray", None)
    user.setdefault("codepad", {})
    user.setdefault("owned_animals", [])
    user.setdefault("team", [])
    user.setdefault("stocks", {})
    return user


async def get_balance(user_id: int) -> int:
    return get_user(user_id)["balance"]


async def update_balance(user_id: int, amount: int):
    user = get_user(user_id)
    user["balance"] += amount
    save_state()


async def set_daily_timestamp(user_id: int):
    user = get_user(user_id)
    user["last_daily"] = datetime.datetime.utcnow().isoformat()
    save_state()


async def get_last_daily(user_id: int):
    return get_user(user_id)["last_daily"]


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your horsenncy balance.")
    async def balance(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        horsenncy = await get_balance(target.id)
        await interaction.response.send_message(
            f"💴 **{target.display_name}** has **{horsenncy} horsenncy**."
        )
    def simulate_stock_prices(self):
        if not hasattr(self, "MARKET_SENTIMENT"):
            self.MARKET_SENTIMENT = 0.0
        self.MARKET_SENTIMENT *= 0.9
        self.MARKET_SENTIMENT += random.uniform(-0.03, 0.03)
        self.MARKET_SENTIMENT = max(min(self.MARKET_SENTIMENT, 1.0), -1.0)
        volatility_wave = random.uniform(0.85, 1.25)
        event = None
        event_multiplier = 1.0
        roll = random.random()
        if roll < 0.004:
            event = "💥 Global Market Crash"
            event_multiplier = random.uniform(0.60, 0.85)
            self.MARKET_SENTIMENT -= random.uniform(0.3, 0.6)
        elif roll < 0.008:
            event = "🚀 Market Euphoria Bubble"
            event_multiplier = random.uniform(1.10, 1.35)
            self.MARKET_SENTIMENT += random.uniform(0.3, 0.5)
        elif roll < 0.015:
            event = "📉 Interest Rate Scare"
            event_multiplier = random.uniform(0.90, 0.97)
            self.MARKET_SENTIMENT -= 0.2
        elif roll < 0.020:
            event = "📈 Strong Economic Growth"
            event_multiplier = random.uniform(1.02, 1.08)
            self.MARKET_SENTIMENT += 0.15
        SECTORS = {
            "tech": ["NAY", "CLVR", "WHIP"],
            "finance": ["UDDR", "STBL"],
            "media": ["WHNY", "PRNC"],
            "transport": ["HOOF", "TROT", "CART"],
            "food": ["HAY", "HNGR", "MINT"],
            "industry": ["BEEF", "SALT", "GLUE"],
            "luxury": ["MANE", "MOO"]
        }
        sector_sentiment = {s: self.MARKET_SENTIMENT + random.uniform(-0.1, 0.1) for s in SECTORS}
        individual = {}
        for symbol in STOCKS:
            r = random.random()
            if r < 0.01:
                individual[symbol] = (1.25, "📈 Breakthrough Discovery")
            elif r < 0.02:
                individual[symbol] = (0.85, "📉 Supply Issues")
            elif r < 0.025:
                individual[symbol] = (1.40, "🚀 Major Insider Buy")
            elif r < 0.03:
                individual[symbol] = (0.75, "💀 Corporate Scandal")
        for symbol, data in STOCKS.items():
            price = data["price"]
            vol = data["volatility"]
            sec = None
            for name, syms in SECTORS.items():
                if symbol in syms:
                    sec = name
                    break
            sec_sent = sector_sentiment.get(sec, 0)
            mom = data.get("momentum", 0.0)
            mom *= 0.85
            mom += random.uniform(-0.02, 0.02)
            revert = (150 - price) / 1500
            rand = random.gauss(0, vol)
            move = rand + (self.MARKET_SENTIMENT * 0.15) + (sec_sent * 0.10) + (mom * 0.25) + revert
            move *= event_multiplier
            if symbol in individual:
                move *= individual[symbol][0]
            new = int(price * (1 + move))
            new = max(new, 1)
            if new < price * 0.80:
                new = int(price * 0.80)
            data["momentum"] = mom
            data["price"] = new
        return event, individual

    @app_commands.command(name="stocks", description="View the ultra-horseyist Horsey Stock Exchange.")
    async def stocks_main(self, interaction: discord.Interaction):
        event, news = self.simulate_stock_prices()
        mood = random.choice(["🐂📈", "🐻📉", "🌪️🤯", "💤", "🔥🔥🔥"])
        def arrow(a, b):
            return "📈" if b > a else "📉" if b < a else "➖"
        def build(uid):
            user = get_user(uid)
            e = discord.Embed(title=f"🏛️ HORSEY STOCK EXCHANGE — {mood}", color=discord.Color.gold())
            desc = ""
            for s, d in STOCKS.items():
                old = d.get("last", d["price"])
                new = d["price"]
                d["last"] = new
                desc += f"**{s}** — *{d['name']}*\n💵 `{new}` horsenncy {arrow(old,new)}\n🎲 Volatility `{int(d['volatility']*100)}%`\n🧮 Market Cap `{new * random.randint(5000,12000):,}`\n\n"
            if event:
                e.add_field(name="🌐 Market Event", value=event, inline=False)
            for sym, (_, msg) in news.items():
                e.add_field(name=f"{sym} News", value=msg, inline=False)
            port = user.setdefault("stocks", {})
            if port:
                total = sum(q * STOCKS[s]["price"] for s, q in port.items())
                p = f"**Portfolio Value:** `{total}` horsenncy\n\n"
                for s, q in port.items():
                    p += f"• {s} × {q} (Value `{q * STOCKS[s]['price']}`)\n"
            else:
                p = "*You own no stocks yet.*"
            e.description = desc
            e.add_field(name="📦 Your Portfolio", value=p, inline=False)
            e.set_footer(text="Press Refresh to update the market prices!")
            return e
        class View(discord.ui.View):
            def __init__(self, uid):
                super().__init__(timeout=80)
                self.uid = uid
            @discord.ui.button(label="Refresh Market", style=discord.ButtonStyle.green)
            async def refresh(self, inter, btn):
                if inter.user.id != self.uid:
                    return await inter.response.send_message("Not your market screen.", ephemeral=True)
                await inter.response.defer()
                for _ in range(3):
                    self.simulate_stock_prices()
                    await asyncio.sleep(0.3)
                await inter.followup.edit_message(message_id=inter.message.id, embed=build(self.uid), view=self)
            @discord.ui.button(label="Buy Stock", style=discord.ButtonStyle.primary)
            async def buy(self, inter, btn):
                if inter.user.id != self.uid:
                    return await inter.response.send_message("Not your terminal.", ephemeral=True)
                await inter.response.send_message("📈 Use `/stocks_buy SYMBOL AMOUNT` to purchase shares.", ephemeral=True)
            @discord.ui.button(label="Sell Stock", style=discord.ButtonStyle.danger)
            async def sell(self, inter, btn):
                if inter.user.id != self.uid:
                    return await inter.response.send_message("Not your terminal.", ephemeral=True)
                await inter.response.send_message("📉 Use `/stocks_sell SYMBOL AMOUNT` to sell shares.", ephemeral=True)
        await interaction.response.send_message(embed=build(interaction.user.id), view=View(interaction.user.id))

    @app_commands.command(name="stocks_buy", description="Buy shares, and win or go broke!")
    async def stocks_buy(self, interaction: discord.Interaction, symbol: str, amount: int):
        symbol = symbol.upper()
        if symbol not in STOCKS:
            return await interaction.response.send_message("❌ Unknown stock symbol.")
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be positive.")
        price = STOCKS[symbol]["price"]
        cost = price * amount
        user = get_user(interaction.user.id)
        if user["balance"] < cost:
            return await interaction.response.send_message(f"💸 You need `{cost}` horsenncy, but you only have `{user['balance']}`.")
        await interaction.response.defer()
        msg = await interaction.followup.send("⌛ Processing order…", wait=True)
        frames = [
            "💼 Connecting to quantum broker…",
            "💼 Syncing multi-dimensional order books…",
            "💼 Bending spacetime for best execution…",
            f"💼 Buying {amount}× {symbol}…",
            "📈 Finalizing universe-safe confirmation…"
        ]
        for f in frames:
            await asyncio.sleep(0.4)
            await msg.edit(content=f)
        user["balance"] -= cost
        port = user.setdefault("stocks", {})
        port[symbol] = port.get(symbol, 0) + amount
        save_state()
        await asyncio.sleep(0.2)
        await msg.edit(content=f"✔️ **ORDER EXECUTED**\n📈 Bought **{amount}× {symbol}**\n💵 Price `{price}`\n💰 Total `{cost}` horsenncy")

    @app_commands.command(name="stocks_sell", description="Sell shares and make that nice money.")
    async def stocks_sell(self, interaction: discord.Interaction, symbol: str, amount: int):
        symbol = symbol.upper()
        if symbol not in STOCKS:
            return await interaction.response.send_message("❌ Unknown stock.")
        user = get_user(interaction.user.id)
        port = user.setdefault("stocks", {})
        if port.get(symbol, 0) < amount:
            return await interaction.response.send_message("❌ You don't own that many shares.")
        price = STOCKS[symbol]["price"]
        earnings = amount * price
        await interaction.response.defer()
        msg = await interaction.followup.send("⌛ Processing sale…", wait=True)
        anim = [
            f"📉 Preparing sell order for {amount}× {symbol}…",
            "📉 Locating buyers across timelines…",
            "📉 Matching inter-universal liquidity…",
            "📉 Executing cosmic trade…"
        ]
        for a in anim:
            await asyncio.sleep(0.4)
            await msg.edit(content=a)
        port[symbol] -= amount
        if port[symbol] <= 0:
            del port[symbol]
        user["balance"] += earnings
        save_state()
        await msg.edit(content=f"✔️ **SALE COMPLETE**\n📉 Sold **{amount}× {symbol}**\n💵 Price `{price}`\n💰 Earnings `{earnings}` horsenncy")


    @app_commands.command(name="blackjack", description="Bet horsenncy on a blackjack game!")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        uid = interaction.user.id
        balance = await get_balance(uid)

        if bet <= 0:
            return await interaction.response.send_message("Bet must be positive.")
        if bet > balance:
            return await interaction.response.send_message("You don't have enough horsenncy.")

        suits = ["♠", "♥", "♦", "♣"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

        deck = [(r, s) for s in suits for r in ranks]
        random.shuffle(deck)

        def draw():
            if not deck:
                new_deck = [(r, s) for s in suits for r in ranks]
                random.shuffle(new_deck)
                deck.extend(new_deck)
            return deck.pop()

        def card_value(rank: str) -> int:
            if rank == "A":
                return 11
            if rank in ["J", "Q", "K"]:
                return 10
            return int(rank)

        def hand_value(hand):
            total = 0
            aces = 0
            for r, _ in hand:
                v = card_value(r)
                total += v
                if r == "A":
                    aces += 1
            while total > 21 and aces > 0:
                total -= 10
                aces -= 1
            return total

        CARD_H = 5

        def build_card(rank: str, suit: str, hidden: bool = False):
            if hidden:
                return [
                    "┌─────┐",
                    "│░░░░░│",
                    "│░░░░░│",
                    "│░░░░░│",
                    "└─────┘",
                ]

            top =  f"┌─────┐"
            r_left = f"{rank:<2}"[:2]
            r_right = f"{rank:>2}"[-2:]
            line2 = f"│{r_left}   │"
            line3 = f"│  {suit}  │"
            line4 = f"│   {r_right}│"
            bottom = "└─────┘"
            return [top, line2, line3, line4, bottom]

        def join_cards(hand, hide_second=False):
            if not hand:
                return "(no cards)"
            lines = [""] * CARD_H
            for idx, (r, s) in enumerate(hand):
                hidden = hide_second and idx == 1
                card_lines = build_card(r, s, hidden=hidden)
                for i in range(CARD_H):
                    lines[i] += card_lines[i] + " "
            return "\n".join(lines)


        gradients = [
            "🟪🟦🟩🟨🟥",
            "🟥🟧🟨🟩🟦",
            "🟦🟩🟨🟧🟥",
        ]


        player = [draw(), draw()]
        dealer = [draw(), draw()]

        pray_boost = get_pray_boost(uid)

        def make_embed(phase: int, game_state: str, reveal_dealer: bool = False):
            dealer_total = hand_value(dealer)
            player_total = hand_value(player)

            gradient = gradients[phase % len(gradients)]

            if reveal_dealer:
                dealer_label = f"[{dealer_total}]"
                dealer_table = join_cards(dealer, hide_second=False)
            else:
                dealer_label = f"[{card_value(dealer[0][0])} + ❓]"
                dealer_table = join_cards(dealer, hide_second=True)

            player_label = f"[{player_total}]"
            player_table = join_cards(player, hide_second=False)

            desc = (
                f"{gradient}\n"
                f"**Bet:** {bet} horsenncy\n\n"
                f"🃏 **Dealer** {dealer_label}\n"
                f"```\n{dealer_table}\n```\n"
                f"👤 **{interaction.user.display_name}** {player_label}\n"
                f"```\n{player_table}\n```\n"
                f"{gradient}\n\n"
                f"{game_state}"
            )

            embed = discord.Embed(
                title="🎴 Blackjack",
                description=desc,
                color=discord.Color.purple()
            )
            return embed

        class BlackjackView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=40)
                self.phase = 0 

            async def update_embed(self, inter: discord.Interaction, state_text: str, reveal: bool = False, keep_view=True):
                embed = make_embed(self.phase, state_text, reveal_dealer=reveal)
                self.phase += 1
                if keep_view:
                    await inter.response.edit_message(embed=embed, view=self)
                else:
                    await inter.response.edit_message(embed=embed, view=None)

            @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
            async def hit(self, button_inter: discord.Interaction, button: discord.ui.Button):
                if button_inter.user.id != uid:
                    return await button_inter.response.send_message("Not your game.", ephemeral=True)

                player.append(draw())
                total = hand_value(player)

                if total > 21:

                    await update_balance(uid, -bet)
                    self.clear_items()
                    await self.update_embed(
                        button_inter,
                        state_text=f"💀 **BUST!** You lost **{bet} horsenncy.**",
                        reveal=True,
                        keep_view=False
                    )
                    return


                await self.update_embed(
                    button_inter,
                    state_text="🕐 Hit taken. Decide your fate…",
                    reveal=False,
                    keep_view=True
                )

            @discord.ui.button(label="Stand", style=discord.ButtonStyle.primary)
            async def stand(self, button_inter: discord.Interaction, button: discord.ui.Button):
                if button_inter.user.id != uid:
                    return await button_inter.response.send_message("Not your game.", ephemeral=True)

                self.clear_items()

                await self.update_embed(
                    button_inter,
                    state_text="🃏 Revealing dealer's hand…",
                    reveal=False,
                    keep_view=True
                )

                msg = button_inter.message

                await asyncio.sleep(0.4)
                embed_mid = make_embed(self.phase, "🃏 The card begins to flip…", reveal_dealer=False)
                self.phase += 1
                await msg.edit(embed=embed_mid, view=self)

                await asyncio.sleep(0.4)

                while hand_value(dealer) < 17:
                    dealer.append(draw())

                p_total = hand_value(player)
                d_total = hand_value(dealer)

                if d_total > 21 or p_total > d_total:
                    winnings = int(bet * pray_boost)
                    await update_balance(uid, winnings)
                    result_text = f"🎉 **You win!** You earned **{winnings} horsenncy.**"
                elif p_total == d_total:
                    result_text = "🤝 **Push!** Your horsenncy is safe this time."
                else:
                    await update_balance(uid, -bet)
                    result_text = f"💀 **Dealer wins.** You lost **{bet} horsenncy.**"

                final_embed = make_embed(self.phase, result_text, reveal_dealer=True)
                self.phase += 1
                await msg.edit(embed=final_embed, view=None)



        view = BlackjackView()
        start_embed = make_embed(phase=0, game_state="🕐 *Game in progress… choose **Hit** or **Stand** below.*", reveal_dealer=False)
        await interaction.response.send_message(embed=start_embed, view=view)

    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        uid = interaction.user.id
        last_daily = await get_last_daily(uid)
        now = datetime.datetime.utcnow()

        if last_daily:
            last = datetime.datetime.fromisoformat(last_daily)
            diff = now - last
            if diff.total_seconds() < 86400:
                remaining = 86400 - diff.total_seconds()
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                await interaction.response.send_message(
                    f"⏳ You already claimed your daily. Try again in **{hours}h {minutes}m**."
                )
                return

        reward = random.randint(100, 300)
        await update_balance(uid, reward)
        await set_daily_timestamp(uid)
        await interaction.response.send_message(
            f"🎁 **Daily Reward:** You received **{reward} horsenncy!**"
        )

    @app_commands.command(name="give", description="Give horsenncy to another user.")
    async def give(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.")
            return

        sender = interaction.user
        sender_balance = await get_balance(sender.id)

        if sender.id == user.id:
            await interaction.response.send_message("You cannot give horsenncy to yourself. No money glitches here.")
            return

        if sender_balance < amount:
            await interaction.response.send_message("You don't have enough horsenncy. Imagine being broke.")
            return

        await update_balance(sender.id, -amount)
        await update_balance(user.id, amount)
        await interaction.response.send_message(
            f"🤝 {sender.display_name} gave **{amount} horsenncy** to {user.display_name}!"
        )

    @app_commands.command(name="coinflip", description="Bet horsenncy on a coin flip.")
    async def coinflip(self, interaction: discord.Interaction, side: str, amount: int):
        side = side.lower()
        if side not in ["heads", "tails"]:
            await interaction.response.send_message("Pick heads or tails.")
            return

        uid = interaction.user.id
        balance = await get_balance(uid)

        if amount <= 0:
            await interaction.response.send_message("Bet must be positive.")
            return

        if balance < amount:
            await interaction.response.send_message("You don't have enough horsenncy.")
            return

        result = random.choice(["heads", "tails"])
        win = result == side
        boost = get_pray_boost(uid)

        if win:
            await update_balance(uid, int(amount * boost))
            await interaction.response.send_message(
                f"🎉 The coin landed on **{result}** — you won **{amount} horsenncy!**"
            )
        else:
            await update_balance(uid, -amount)
            await interaction.response.send_message(
                f"💀 The coin landed on **{result}** — you lost **{amount} horsenncy.**"
            )

    @app_commands.command(name="pray", description="Pray to the overlord Horsey.")
    async def pray(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)

        now = datetime.datetime.utcnow()

        last = user.get("last_pray")
        if last:
            last_time = datetime.datetime.fromisoformat(last)
            diff = (now - last_time).total_seconds()
            if diff < 600:  
                remaining = int(600 - diff)
                minutes = remaining // 60
                seconds = remaining % 60
                return await interaction.response.send_message(
                    f"⏳ You must wait **{minutes}m {seconds}s** before praying again. Praying too much will be suspicious."
                )

        user["last_pray"] = now.isoformat()

        if random.random() < 0.10:
            user["pray"] = 0
            save_state()
            corrupted_messages = [
                "💀 **The Horsey god is displeased.**",
                "🔥 A divine hoof stomps the ground. Your prayers crumble.",
                "🌫️ A cold neigh echoes... your faith collapses.",
                "⚡ Your prayer backfires violently. You hear a distant moo.",
            ]
            return await interaction.response.send_message(
                random.choice(corrupted_messages)
                + "\nYour **prayer points have been reset to 0.**"
            )

        user["pray"] += 1
        save_state()

        blessing_messages = [
            "🌟 The overlord Horsey respects your worship.",
            "🐴 A divine neigh echoes approvingly.",
            "✨ You feel cosmic Horsey energy flowing through you.",
            "🌤️ A gentle hoof pats your soul. Horsey invicta.",
            "🎇 Reality flickers. Horsey approves."
        ]
        msg = random.choice(blessing_messages)

        await interaction.response.send_message(
            f"{msg}\nYou now have **{user['pray']} prayer points!**"
        )

    
    @app_commands.command(name="leaderboard", description="Top players by horsenncy.")
    async def leaderboard(self, interaction: discord.Interaction):

        users = state["users"]

        if not users:
            await interaction.response.send_message("No data yet.")
            return

        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1]["balance"],
            reverse=True
        )[:10]

        lines = []
        rank = 1

        for uid, data in sorted_users:
            uid_int = int(uid)
            balance = data["balance"]

            member = None
            name = None

            if interaction.guild:
                member = interaction.guild.get_member(uid_int)

            if not member:
                member = interaction.client.get_user(uid_int)

            if not member:
                try:
                    member = await interaction.client.fetch_user(uid_int)
                except:
                    member = None

            name = member.display_name if member else f"User {uid}"

            lines.append(f"**#{rank}** — {name}: **{balance} horsenncy**")
            rank += 1

        await interaction.response.send_message(
            "🏆 | **Top 10 Richest Users**\n" + "\n".join(lines)
        )
    @app_commands.command(name="team", description="Manage your battle team.")
    @app_commands.describe(
        action="add, remove, or list",
        index="Index of the animal to add/remove (use /team list first)"
    )
    async def team(self, interaction: discord.Interaction, action: str, index: int = None):
        uid = interaction.user.id
        user = get_user(uid)

        action = action.lower()
        owned = user.setdefault("owned_animals", [])
        team = user.setdefault("team", [])

        if action not in ["add", "remove", "list"]:
            return await interaction.response.send_message("❌ Invalid action. Use: add / remove / list")

        if action == "list":
            if not owned:
                return await interaction.response.send_message("📭 You own no animals yet. Hunt some first!")

            msg = "😼 **Your Owned Animals**\n"
            for i, a in enumerate(owned):
                msg += f"`{i}` — {a['name']} ({a['rarity']}, {a['strength']} strength)\n"

            msg += "\n🛡 **Your Team (max 8)**\n"
            if team:
                for t in team:
                    msg += f"- {t['name']} ({t['rarity']}, {t['strength']} strength)\n"
            else:
                msg += "*Your team is empty.*"

            return await interaction.response.send_message(msg)

        if action == "add":
            if index is None:
                return await interaction.response.send_message("Specify the animal index.")

            if index < 0 or index >= len(owned):
                return await interaction.response.send_message("Invalid index.")

            if len(team) >= 8:
                return await interaction.response.send_message("❌ Your team is full (8 animals max).")

            animal = owned[index]
            team.append(animal)
            save_state()

            return await interaction.response.send_message(
                f"✔️ **{animal['name']}** has been added to your team!"
            )

        if action == "remove":
            if index is None:
                return await interaction.response.send_message("Specify the team index.")

            if index < 0 or index >= len(team):
                return await interaction.response.send_message("Invalid team index.")

            removed = team.pop(index)
            save_state()

            return await interaction.response.send_message(
                f"❌ Removed **{removed['name']}** from your battle team."
            )


    @app_commands.command(name="hunt", description="Go hunting with a rich loot table.")
    async def hunt(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user = get_user(user_id)
        cd = get_cooldown(user_id, "hunt_cooldown")
        now = datetime.datetime.utcnow()
        if cd and now < cd:
            remaining = cd - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return await interaction.response.send_message(
                f"🦌 The wilderness is too dangerous right now!\n"
                f"Try hunting again in **{hours}h {minutes}m**."
            )
        loot_table = [
                ("🐀 Rat", 10, "Common"),
                ("🐁 Field Mouse", 12, "Common"),
                ("🐦 Sparrow", 15, "Common"),
                ("🐇 Bunny", 20, "Common"),
                ("🦊 Fox", 25, "Common"),
                ("🦝 Raccoon", 18, "Common"),
                ("🐿️ Squirrel", 17, "Common"),
                ("🦤 Dodo (how??)", 22, "Common"),
                ("🐔 Chicken", 19, "Common"),
                ("🦆 Duck", 23, "Common"),
                ("🐄 Cow (baby)", 30, "Common"),
                ("🐕 Stray Dog", 28, "Common"),
                ("🐈 Wild Cat", 29, "Common"),
                ("🦮 Hunting Dog", 33, "Common"),
                ("🐖 Piglet", 26, "Common"),
                ("🦢 Swan", 21, "Common"),
                ("🦉 Barn Owl", 27, "Common"),
                ("🦜 Parrot", 24, "Common"),
                ("🦎 Lizard", 14, "Common"),
                ("🐍 Small Snake", 16, "Common"),
                ("🦌 Deer", 70, "Uncommon"),
                ("🐗 Wild Hog", 65, "Uncommon"),
                ("🦃 Turkey", 55, "Uncommon"),
                ("🐐 Mountain Goat", 60, "Uncommon"),
                ("🐓 Rooster", 48, "Uncommon"),
                ("🦢 Giant Swan", 50, "Uncommon"),
                ("🦨 Skunk", 52, "Uncommon"),
                ("🐊 Baby Crocodile", 80, "Uncommon"),
                ("🐺 Wolf", 85, "Uncommon"),
                ("🦫 Beaver", 57, "Uncommon"),
                ("🦦 Otter", 68, "Uncommon"),
                ("🐅 Young Tiger", 75, "Uncommon"),
                ("🦘 Wallaby", 58, "Uncommon"),
                ("🐏 Ram", 72, "Uncommon"),
                ("🦅 Eagle", 88, "Uncommon"),
                ("🦩 Flamingo", 63, "Uncommon"),
                ("🦚 Peacock", 66, "Uncommon"),
                ("🦡 Badger", 71, "Uncommon"),
                ("🦤 Giant Dodo", 90, "Uncommon"),
                ("🦭 Mini Seal", 69, "Uncommon"),
                ("🐻 Bear", 180, "Rare"),
                ("🐅 Tiger", 160, "Rare"),
                ("🦏 Rhino (baby)", 150, "Rare"),
                ("🦍 Gorilla", 170, "Rare"),
                ("🦬 Buffalo", 155, "Rare"),
                ("🐘 Baby Elephant", 140, "Rare"),
                ("🦌 Elk", 145, "Rare"),
                ("🦈 Reef Shark", 175, "Rare"),
                ("🐊 Crocodile", 190, "Rare"),
                ("🦒 Giraffe", 165, "Rare"),
                ("🦛 Hippo", 185, "Rare"),
                ("🐆 Leopard", 200, "Rare"),
                ("🦃 Mutant Turkey", 130, "Rare"),
                ("🦜 Tropical Macaw", 120, "Rare"),
                ("🦢 Enraged Swan", 125, "Rare"),
                ("🦡 Alpha Badger", 150, "Rare"),
                ("🦭 Great Seal", 160, "Rare"),
                ("🐐 Demon Goat", 140, "Rare"),
                ("🦣 Mammoth Calf", 180, "Rare"),
                ("🦦 Sea Otter King", 190, "Rare"),
                ("🐉 Baby Dragon", 320, "Epic"),
                ("🦅 Roc Hatchling", 300, "Epic"),
                ("🐲 Mini Wyvern", 260, "Epic"),
                ("🦂 Giant Scorpion", 240, "Epic"),
                ("🦖 Young T-Rex", 350, "Epic"),
                ("🦕 Brontosaurus Hatchling", 330, "Epic"),
                ("🦍 Titan Gorilla", 310, "Epic"),
                ("🐲 Lava Drake", 340, "Epic"),
                ("🦈 Megalodon Pup", 325, "Epic"),
                ("🐺 Dire Wolf", 285, "Epic"),
                ("🦄 Unicorn Fawn", 300, "Epic"),
                ("🐉 Forest Dragonling", 290, "Epic"),
                ("🐐 Chaos Goat", 260, "Epic"),
                ("🦅 Storm Eagle", 270, "Epic"),
                ("🐗 Demon Boar", 255, "Epic"),
                ("🐆 Shadow Panther", 295, "Epic"),
                ("🦇 Vampire Batlord", 275, "Epic"),
                ("🐍 Titan Serpent", 310, "Epic"),
                ("🦎 Elder Lizard", 265, "Epic"),
                ("🐘 Giant Elephant Spirit", 300, "Epic"),
                ("🐉 Ancient Dragon", 700, "Legendary"),
                ("🐲 Celestial Wyvern", 680, "Legendary"),
                ("🦅 Thunder Roc", 650, "Legendary"),
                ("🦄 Eternal Unicorn", 640, "Legendary"),
                ("🐺 Moon Wolf", 590, "Legendary"),
                ("🐆 Galaxy Panther", 620, "Legendary"),
                ("🦂 King Scorpion", 575, "Legendary"),
                ("🦖 Elder T-Rex", 750, "Legendary"),
                ("🦕 Prime Bronto", 770, "Legendary"),
                ("🐊 Abyssal Crocodile", 800, "Legendary"),
                ("🌑 Shadow Colossus", 1500, "Mythic"),
                ("🌋 Volcano Titan", 1800, "Mythic"),
                ("🌪️ Storm Leviathan", 2000, "Mythic"),
                ("🌌 Cosmic Dragon", 2500, "Mythic"),
                ("🔥 Phoenix", 3000, "Mythic")
        ]

        weights = [
                *([35] * 20),
                *([15] * 20),
                *([5] * 20),
                *([1.5] * 20),
                *([0.35] * 10),
                *([0.1] * 5)
        ]

        animal, base_reward, rarity = random.choices(loot_table, weights=weights, k=1)[0]
        strength = base_reward
        escape_chance = min(0.75, max(0.10, strength / 3000))

        if random.random() < escape_chance:
            set_cooldown(user_id, "hunt_cooldown", 5)
            return await interaction.response.send_message(
                f"💨 **The {animal} escaped!**\n"
                f"You're exhausted and must rest for **5 hours**."
            )


        crit = random.random() < 0.10
        final_reward = base_reward * (2 if crit else 1)
        boost = get_pray_boost(user_id)
        final_reward = int(final_reward * boost)


        if random.random() < 0.05:
            return await interaction.response.send_message("💨 You missed everything. Skill issue.")

        await update_balance(user_id, final_reward)
        owned = user.setdefault("owned_animals", [])
        owned.append({
            "name": animal,
            "rarity": rarity,
            "strength": base_reward
        })
        save_state()
        await interaction.response.send_message(
            f"🏹 You hunted a **{animal}** ({rarity}) and earned **{final_reward} horsenncy!**"
            + (" 💥 **CRITICAL HIT!**" if crit else "")
        )
    @app_commands.command(name="fish", description="Go fishing with expanded loot!")
    async def fish(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user = get_user(user_id)
        cd = get_cooldown(user_id, "fish_cooldown")
        now = datetime.datetime.utcnow()
        if cd and now < cd:
            remaining = cd - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            return await interaction.response.send_message(
                f"🛑 Your **fishing rod is broken**! Try again in **{hours}h {minutes}m**."
            )
        fish_table = [
                ("🐟 Common Carp", 15, "Common"),
                ("🐠 Clownfish", 25, "Common"),
                ("🦐 Shrimp", 10, "Common"),
                ("🐠 Sardine", 12, "Common"),
                ("🐡 Sunfish", 14, "Common"),
                ("🐟 Anchovy", 11, "Common"),
                ("🐠 Guppy", 13, "Common"),
                ("🐟 Minnow", 10, "Common"),
                ("🦑 Baby Squid", 18, "Common"),
                ("🦀 Small Crab", 20, "Common"),
                ("🐚 Seashell Fragment", 8, "Common"),
                ("🐌 Sea Snail", 17, "Common"),
                ("🪼 Tiny Jellyfish", 16, "Common"),
                ("🐠 Bluegill", 19, "Common"),
                ("🐟 Perch", 22, "Common"),
                ("🐠 Butterflyfish", 21, "Common"),
                ("🐟 Tadpole", 9, "Common"),
                ("🦐 Krill Cluster", 12, "Common"),
                ("🐡 Baby Blowfish", 18, "Common"),
                ("🦦 Wet Fur Scrap", 7, "Common"),
                ("🐟 Bass", 30, "Uncommon"),
                ("🐠 Neon Tetra", 35, "Uncommon"),
                ("🐟 Trout", 40, "Uncommon"),
                ("🦐 Tiger Shrimp", 36, "Uncommon"),
                ("🐡 Spiked Puffer", 50, "Uncommon"),
                ("🐠 Angel Fish", 42, "Uncommon"),
                ("🐟 Golden Carp", 45, "Uncommon"),
                ("🦑 Squid", 48, "Uncommon"),
                ("🦀 Stone Crab", 38, "Uncommon"),
                ("🐚 Conch Shell", 33, "Uncommon"),
                ("🐠 Zebra Fish", 37, "Uncommon"),
                ("🐟 Salmon", 55, "Uncommon"),
                ("🐠 Swordtail", 34, "Uncommon"),
                ("🐡 Banded Puffer", 47, "Uncommon"),
                ("🪼 Pink Jellyfish", 52, "Uncommon"),
                ("🐠 Moorish Idol", 41, "Uncommon"),
                ("🐟 Catfish", 49, "Uncommon"),
                ("🦀 Hermit Crab", 44, "Uncommon"),
                ("🐠 Rainbow Fish", 53, "Uncommon"),
                ("🦐 Jumbo Shrimp", 39, "Uncommon"),
                ("🐙 Octopus", 90, "Rare"),
                ("🦞 Lobster", 120, "Rare"),
                ("🐠 Lionfish", 110, "Rare"),
                ("🦑 Giant Squidling", 105, "Rare"),
                ("🐡 Balloon Puffer", 95, "Rare"),
                ("🦀 King Crab", 130, "Rare"),
                ("🐟 Electric Eel", 125, "Rare"),
                ("🐋 Baby Whale", 140, "Rare"),
                ("🐬 Dolphin Tooth", 135, "Rare"),
                ("🦈 Reef Shark", 150, "Rare"),
                ("🐠 Koi Spirit", 145, "Rare"),
                ("🐙 Ink Demon Octopus", 160, "Rare"),
                ("🐟 Steelhead Fish", 115, "Rare"),
                ("🦞 Blood Lobster", 155, "Rare"),
                ("🐡 Toxic Puffer", 100, "Rare"),
                ("🪼 Stinger Jellyfish", 120, "Rare"),
                ("🐠 Ghost Fish", 143, "Rare"),
                ("🐋 Leviathan Scale", 170, "Rare"),
                ("🦀 Royal Crab", 155, "Rare"),
                ("🐬 Echo Dolphin", 165, "Rare"),
                ("🦈 Shark", 250, "Epic"),
                ("🐋 Leviathan Fragment", 300, "Epic"),
                ("🐉 Abyss Dragonfish", 280, "Epic"),
                ("🐙 Titan Octopus", 260, "Epic"),
                ("🦑 Krakenling", 275, "Epic"),
                ("🐡 Astro Puffer", 245, "Epic"),
                ("🦞 Cosmic Lobster", 290, "Epic"),
                ("🐟 Thunder Eel", 255, "Epic"),
                ("🐬 Celestial Dolphin", 310, "Epic"),
                ("🦀 Void Crab", 265, "Epic"),
                ("🐠 Crystal Koi", 295, "Epic"),
                ("🪼 Nebula Jellyfish", 270, "Epic"),
                ("🐚 Soul Shell", 240, "Epic"),
                ("🐋 Abyss Whale", 300, "Epic"),
                ("🦈 Ironjaw Shark", 250, "Epic"),
                ("🐡 Galactic Puffer", 320, "Epic"),
                ("🐙 Dimensional Octopus", 305, "Epic"),
                ("🦑 Arcane Squid", 285, "Epic"),
                ("🐬 Star Whale Cub", 330, "Epic"),
                ("🐋 Tidal Leviathan", 350, "Epic"),
                ("🐲 Sea Dragon", 450, "Legendary"),
                ("🦈 Megalodon", 500, "Legendary"),
                ("🐋 Leviathan", 600, "Legendary"),
                ("🐙 Kraken", 550, "Legendary"),
                ("🐉 Ocean Serpent", 650, "Legendary"),
                ("🦑 Colossal Squid", 520, "Legendary"),
                ("🐬 Astral Dolphin", 580, "Legendary"),
                ("🦞 Mythic Lobster", 490, "Legendary"),
                ("🐟 Thunderbird Fish", 470, "Legendary"),
                ("🪼 Radiant Jellyfish", 530, "Legendary"),
                ("🌊 Tidal Colossus", 900, "Mythic"),
                ("🌌 Cosmic Leviathan", 1100, "Mythic"),
                ("🔥 Phoenix Salmon", 1300, "Mythic"),
                ("⚡ Storm Serpent", 1500, "Mythic"),
                ("🜂 Eternal Flamefish", 2000, "Mythic")
        ]

        weights = [
                *([35] * 20),
                *([20] * 20),
                *([8] * 20),
                *([2] * 20),
                *([0.4] * 10),
                *([0.1] * 5)
        ]

        fish, value, rarity = random.choices(fish_table, weights=weights, k=1)[0]

        strength = value
        break_chance = min(0.75, max(0.10, strength / 2000))

        if random.random() < break_chance:
            set_cooldown(user_id, "fish_cooldown", 5)
            return await interaction.response.send_message(
                f"💥 **Your fishing rod snapped while catching {fish}!**\n"
                f"⏳ You can't fish for **5 hours**."
            )

        jackpot = random.random() < 0.05
        if jackpot:
            value *= 5

        boost = get_pray_boost(user_id)
        value = int(value * boost)
        await update_balance(user_id, value)

        await interaction.response.send_message(
            f"🎣 You caught **{fish}** ({rarity}) worth **{value} horsenncy!**"
            + (" 🎉 **JACKPOT CATCH! x5 VALUE!**" if jackpot else "")
        )
    @app_commands.command(name="battle", description="Fight monsters RPG-style!")
    async def battle(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)
        monsters = [
                ("Slime", 30, 0.70),
                ("Bandit", 50, 0.60),
                ("Goblin", 80, 0.55),
                ("Wolf", 75, 0.58),
                ("Skeleton", 65, 0.62),
                ("Zombie", 70, 0.60),
                ("Orc Grunt", 85, 0.54),
                ("Giant Rat", 45, 0.66),
                ("Bat Swarm", 40, 0.68),
                ("Stone Imp", 90, 0.53),
                ("Minotaur", 140, 0.45),
                ("Forest Troll", 120, 0.48),
                ("Sand Golem", 110, 0.50),
                ("Ice Wraith", 130, 0.46),
                ("Dark Ranger", 115, 0.49),
                ("Cave Spider", 95, 0.52),
                ("Fire Imp", 105, 0.51),
                ("Bog Lurker", 100, 0.52),
                ("Harpy", 125, 0.47),
                ("Sea Serpentling", 135, 0.45),
                ("Demon", 250, 0.30),
                ("Ogre", 190, 0.38),
                ("Frost Giantling", 210, 0.35),
                ("Lava Hound", 230, 0.33),
                ("Vampire Thrall", 160, 0.42),
                ("Shadow Assassin", 175, 0.40),
                ("Wraith", 185, 0.39),
                ("Ghoul", 155, 0.43),
                ("Stone Gargoyle", 200, 0.36),
                ("Thunder Boar", 170, 0.41),
                ("Ancient Dragon", 500, 0.15),
                ("Flame Titan", 480, 0.16),
                ("Storm Colossus", 520, 0.14),
                ("Frost Wyvern", 450, 0.17),
                ("Magma Serpent", 430, 0.18),
                ("Astral Chimera", 540, 0.13),
                ("Elder Treant", 460, 0.17),
                ("Abyss Drake", 550, 0.12),
                ("Crystal Golem", 490, 0.15),
                ("Celestial Sphinx", 570, 0.12),
                ("Cursed Knight", 260, 0.32),
                ("Plague Bringer", 280, 0.31),
                ("Warlock", 240, 0.34),
                ("Nightmare Horse", 275, 0.30),
                ("Bone Colossus", 300, 0.28),
                ("Spectral Vanguard", 265, 0.31),
                ("Void Revenant", 320, 0.26),
                ("Flame Wraith", 290, 0.29),
                ("Rune Guardian", 310, 0.27),
                ("Fallen Hero", 255, 0.32),
                ("Abyss Walker", 350, 0.24),
                ("Dread Knight", 370, 0.23),
                ("Time Eater", 390, 0.22),
                ("Reality Shifter", 420, 0.20),
                ("Eternal Harvester", 410, 0.21),
                ("Corrupted Paladin", 345, 0.25),
                ("Blight Dragonling", 385, 0.23),
                ("Phantom Rider", 330, 0.25),
                ("Soul Burner", 365, 0.24),
                ("Astral Blade Spirit", 405, 0.21),
                ("Kraken Spawn", 310, 0.27),
                ("Sea Wraith", 330, 0.26),
                ("Tidebreaker Golem", 350, 0.24),
                ("Saltwater Leviathan", 380, 0.22),
                ("Coral Serpent", 295, 0.29),
                ("Drowned King", 420, 0.19),
                ("Abyssal Siren", 360, 0.23),
                ("Brine Demon", 340, 0.25),
                ("Storm Sailor Ghost", 325, 0.26),
                ("Whirlpool Elemental", 400, 0.20),
                ("Lich", 600, 0.10),
                ("Archdemon", 650, 0.08),
                ("Void Titan", 700, 0.07),
                ("Elder Lich", 680, 0.09),
                ("Doom Hydra", 720, 0.06),
                ("Worldspine Serpent", 750, 0.05),
                ("Titanic Minotaur", 670, 0.09),
                ("Nether Colossus", 740, 0.05),
                ("Cataclysm Dragon", 800, 0.04),
                ("Oblivion Phoenix", 820, 0.03),
                ("Abyss Emperor", 900, 0.02),
                ("Planetbreaker Golem", 950, 0.015),
                ("Cosmic Devourer", 1000, 0.01),
                ("Starborn Wyrm", 880, 0.02),
                ("Infinity Chimera", 920, 0.015),
                ("Void Sovereign", 1100, 0.009),
                ("Chrono Seraph", 1050, 0.011),
                ("Eclipse Dragon", 1150, 0.008),
                ("Oblivion Titan", 1200, 0.007),
                ("The Endbringer", 1500, 0.005),
                ("World Eater Zorvath", 2000, 0.003),
                ("Dimensional Anomaly", 1750, 0.004),
                ("Dread Star Serpent", 1600, 0.0045),
                ("The Final Horror", 2500, 0.002)
        ]

        if random.random() < 0.03:
            monster = ("🌑 World Eater Horsey", 1500, 0.05)
        else:
            monster = random.choice(monsters)

        name, reward, win_rate = monster
        boost = get_pray_boost(uid)
        win_rate *= boost
        team = user.setdefault("team", [])

        team_strength = sum(a["strength"] for a in team)

        team_bonus = min(0.25, team_strength / 8000)

        win_rate *= (1 + team_bonus)
        win_rate = min(win_rate, 0.98)


        win = random.random() < win_rate

        crit = random.random() < 0.12  

        if win:
            final_reward = reward * (2 if crit else 1)
            final_reward = int(final_reward * boost)
            await update_balance(uid, final_reward)
            await interaction.response.send_message(
                f"⚔️ You defeated **{name}** and earned **{final_reward} horsenncy!**"
                + (" 💥 **CRITICAL STRIKE!**" if crit else "")
            )
        else:
            loss = random.randint(25, 80)
            await update_balance(uid, -loss)
            await interaction.response.send_message(
                f"💀 **{name}** destroyed you. You dropped **{loss} horsenncy**."
            )
    @app_commands.command(name="crime", description="Commit a risky crime!")
    async def crime(self, interaction: discord.Interaction):
        uid = interaction.user.id

        crimes = [
                ("Pickpocketed a tourist", 30),
                ("Stole a bike", 45),
                ("Hacked an ATM", 80),
                ("Robbed a jewelry store", 150),
                ("Embezzled government funds", 300),
                ("Robbed the central bank", 600),
                ("Snatched a purse", 25),
                ("Shoplifted snacks", 20),
                ("Stole a phone", 40),
                ("Robbed a gas station", 70),
                ("Forged lottery tickets", 90),
                ("Scammed someone online", 85),
                ("Sold counterfeit shoes", 60),
                ("Stole a wallet on the bus", 35),
                ("Pickpocketed a businessman", 55),
                ("Hacked a vending machine", 50),
                ("Stole cryptocurrency keys", 100),
                ("Robbed a mini-mart", 65),
                ("Sold fake concert tickets", 95),
                ("Framed someone for a crime", 120),
                ("Stole military rations", 45),
                ("Stole a police radio", 50),
                ("Committed tax fraud", 150),
                ("Sold stolen laptops", 110),
                ("Pirated paid software", 40),
                ("Broke into a warehouse", 130),
                ("Hijacked a scooter", 30),
                ("Ran an illegal raffle", 70),
                ("Stole rare horsenncy", 90),
                ("Scammed a streamer donation", 75),
                ("Illegally siphoned gas", 65),
                ("Cracked a safe", 160),
                ("Sold bootleg movies", 35),
                ("Stole a golden statue", 210),
                ("Counterfeited documents", 140),
                ("Sold stolen credit cards", 180),
                ("Hacked school servers", 110),
                ("Bribed a guard", 50),
                ("Smuggled rare spices", 95),
                ("Illegally resold medicine", 130),
                ("Fraudulently used coupons", 28),
                ("Stole a luxury handbag", 140),
                ("Ran a fake charity scam", 200),
                ("Stole high-end electronics", 175),
                ("Smuggled exotic birds", 150),
                ("Stole casino chips", 125),
                ("Sold hacked accounts", 105),
                ("Stole a delivery package", 45),
                ("Hijacked a delivery truck", 190),
                ("Sold fake NFTs", 160),
                ("Cloned credit cards", 220),
                ("Spoofed bank emails", 180),
                ("Stole a diamond ring", 155),
                ("Sold counterfeit gold", 170),
                ("Hacked medical records", 140),
                ("Stole a rare painting", 230),
                ("Robbed a poker game", 175),
                ("Sold government secrets", 300),
                ("Stole a rare artifact", 260),
                ("Hacked airport Wi-Fi", 90),
                ("Robbed a crypto miner", 210),
                ("Stole confidential files", 130),
                ("Ran a phishing scheme", 120),
                ("Smuggled illegal fireworks", 60),
                ("Organized a street scam", 70),
                ("Hijacked a taxi", 55),
                ("Stole from a church donation box", 40),
                ("Stole a vintage guitar", 100),
                ("Sold fake IDs", 95),
                ("Hacked a YouTuber account", 140),
                ("Broke into a luxury home", 200),
                ("Stole casino prize money", 175),
                ("Ran a loan shark ring", 180),
                ("Robbed a food truck", 90),
                ("Bribed a customs officer", 160),
                ("Smuggled rare minerals", 190),
                ("Hacked cryptocurrency wallets", 250),
                ("Stole a high-end PC", 150),
                ("Organized a black-market auction", 275),
                ("Stole classified intel", 240),
                ("Manipulated stock trades", 300),
                ("Robbed an armored truck", 400),
                ("Completely drained a bank account", 500),
                ("Illegally sold weapons", 260),
                ("Broke into a government bunker", 350),
                ("Stole a prototype device", 320),
                ("Extorted an influencer", 210),
                ("Hacked a corporation", 330),
                ("Hijacked a private yacht", 380),
                ("Stole a luxury sports car", 420),
                ("Blackmailed a politician", 450),
                ("Robbed a mafia vault", 600),
                ("Hijacked a crypto exchange", 700),
                ("Broke into a maximum-security vault", 900),
                ("Stole an alien artifact", 1000),
                ("Cracked an interdimensional bank", 1500)
        ]

        success_rate = 0.45
        action, reward = random.choice(crimes)
        boost = get_pray_boost(uid) 
        reward = int(reward * boost)

        if random.random() < 0.02:
            reward *= 10
            await update_balance(uid, reward)
            return await interaction.response.send_message(
                f"💰💰 **LEGENDARY HEIST!** You stole **{reward} horsenncy!!!**"
            )
        success_rate *= boost
        success_rate = min(success_rate, 0.90)
        
        if random.random() < success_rate:
            await update_balance(uid, reward)
            return await interaction.response.send_message(
                f"🦹 You **{action}** and earned **{reward} horsenncy!**"
            )
        else:
            user = get_user(uid)
            balance = user["balance"]

            if random.random() < 0.75:
                if balance > 0:
                    loss = balance
                    user["balance"] = 0
                else:
                    loss = 0

                save_state()

                msg = "🚨 Police caught you! They seized ALL your horsenncy!"
                return await interaction.response.send_message(
                    f"{msg} You lost **{loss} horsenncy.**"
                )

            else:
                loss = random.randint(30, 120)
                msg = "🚓 You got caught."

            await update_balance(uid, -loss)
            return await interaction.response.send_message(
                f"{msg} You lost **{loss} horsenncy.**"
            )


    @app_commands.command(name="slots", description="Spin the ultra deluxe 3x3 slot machine!")
    async def slots(self, interaction: discord.Interaction, bet: int):
        uid = interaction.user.id
        balance = await get_balance(uid)

        if bet <= 0:
            return await interaction.response.send_message("Bet must be positive.")
        if bet > balance:
            return await interaction.response.send_message("You don't have enough horsenncy!")

        icons = ["🍒", "🍋", "🍇", "⭐", "💎", "🔥"]
        boost = get_pray_boost(uid)

        await interaction.response.defer()

        grid = [[random.choice(icons) for _ in range(3)] for _ in range(3)]

        gradients = [
            "🟪🟦🟩🟨🟥",
            "🟥🟧🟨🟩🟦",
            "🟦🟩🟨🟧🟥",
        ]

        def build_grid_display(reveal_cols: int):
            lines = []
            for r in range(3):
                row_symbols = []
                for c in range(3):
                    if c <= reveal_cols:
                        row_symbols.append(grid[r][c])
                    else:
                        row_symbols.append("⬛")
                lines.append(" | ".join(row_symbols))
            return "┌───────────────┐\n" + "\n".join(f"│ {line} │" for line in lines) + "\n└───────────────┘"

        async def edit_spin_state(msg, step: int, reveal_cols: int, status: str):
            gradient = gradients[step % len(gradients)]
            grid_text = build_grid_display(reveal_cols)
            desc = (
                f"{gradient}\n"
                f"**Bet:** {bet} horsenncy\n\n"
                f"🎰 **Slots**\n"
                f"```{grid_text}```\n"
                f"{gradient}\n\n"
                f"{status}"
            )
            embed = discord.Embed(
                title="🎰 Ultra Slots",
                description=desc,
                color=discord.Color.purple()
            )
            await msg.edit(embed=embed)

        gradient0 = gradients[0]
        start_grid = build_grid_display(-1)
        start_desc = (
            f"{gradient0}\n"
            f"**Bet:** {bet} horsenncy\n\n"
            f"🎰 **Slots**\n"
            f"```{start_grid}```\n"
            f"{gradient0}\n\n"
            f"Pulling the lever…"
        )
        start_embed = discord.Embed(
            title="🎰 Ultra Slots",
            description=start_desc,
            color=discord.Color.purple()
        )
        msg = await interaction.followup.send(embed=start_embed, wait=True)

        await asyncio.sleep(0.4)
        await edit_spin_state(msg, 0, 0, "Reel 1 is spinning violently…")
        await asyncio.sleep(0.5)
        await edit_spin_state(msg, 1, 1, "Reel 2 is trying to escape reality…")
        await asyncio.sleep(0.5)
        await edit_spin_state(msg, 2, 2, "Final reel locking in your fate…")
        await asyncio.sleep(0.5)

        cols = [[grid[r][c] for r in range(3)] for c in range(3)]
        diag1 = [grid[i][i] for i in range(3)]
        diag2 = [grid[i][2 - i] for i in range(3)]

        reward = 0
        lines_hit = []

        def all_same(seq):
            return seq[0] == seq[1] == seq[2]

        god_event = False
        if random.random() < 0.004:
            god_event = True
            reward = int(bet * 40 * boost)
            lines_hit.append("🌌 **HORSEY GOD JACKPOT x40!**")

        if not god_event:
            for idx, row in enumerate(grid):
                if all_same(row):
                    sym = row[0]
                    if sym == "🔥":
                        reward = int(bet * 15 * boost)
                        lines_hit.append(f"🔥 **Mythic Blazing Triple (row {idx+1}) x15!**")
                    elif sym == "💎":
                        reward = int(bet * 10 * boost)
                        lines_hit.append(f"💎 **Ultra Diamond Triple (row {idx+1}) x10!**")
                    else:
                        reward = int(bet * 6 * boost)
                        lines_hit.append(f"✨ **Row {idx+1} Triple Match x6!**")

            if reward == 0:
                base_multi = 0

                for idx, col in enumerate(cols):
                    if all_same(col):
                        sym = col[0]
                        if sym == "🔥":
                            base_multi = max(base_multi, 8)
                            lines_hit.append(f"🔥 Column {idx+1} triple x8!")
                        elif sym == "💎":
                            base_multi = max(base_multi, 6)
                            lines_hit.append(f"💎 Column {idx+1} triple x6!")
                        else:
                            base_multi = max(base_multi, 4)
                            lines_hit.append(f"Column {idx+1} triple x4!")

                for name, diag in [("↘", diag1), ("↙", diag2)]:
                    if all_same(diag):
                        sym = diag[0]
                        if sym == "🔥":
                            base_multi = max(base_multi, 10)
                            lines_hit.append(f"🔥 Diagonal {name} triple x10!")
                        elif sym == "💎":
                            base_multi = max(base_multi, 8)
                            lines_hit.append(f"💎 Diagonal {name} triple x8!")
                        else:
                            base_multi = max(base_multi, 5)
                            lines_hit.append(f"Diagonal {name} triple x5!")

                if base_multi > 0:
                    reward = int(bet * base_multi * boost)

        if reward <= 0 and not god_event:
            await update_balance(uid, -bet)
            final_status = f"❌ **No winning lines.** You lost **{bet} horsenncy.**"
        else:
            await update_balance(uid, reward)
            if god_event:
                final_status = (
                    f"🌌 **HORSEY GOD INTERVENTION!**\n"
                    f"You are blessed with **{reward} horsenncy!**"
                )
            else:
                lines_text = "\n".join(lines_hit) if lines_hit else "Somehow you won but I forgot why."
                final_status = (
                    f"{lines_text}\n\n"
                    f"💰 You earned **{reward} horsenncy!**"
                )

        final_grid = build_grid_display(2)
        gradient_final = gradients[random.randint(0, len(gradients) - 1)]
        final_desc = (
            f"{gradient_final}\n"
            f"**Bet:** {bet} horsenncy\n\n"
            f"🎰 **SLOTS: Final Result**\n"
            f"```{final_grid}```\n"
            f"{gradient_final}\n\n"
            f"{final_status}"
        )
        final_embed = discord.Embed(
            title="🎰 SLOTS: Result",
            description=final_desc,
            color=discord.Color.purple()
        )
        await msg.edit(embed=final_embed)

    @app_commands.command(name="work", description="Work jobs with promotions & raises!")
    async def work(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user = get_user(uid)

        last = user.get("last_work")
        now = datetime.datetime.utcnow()

        if last:
            last_time = datetime.datetime.fromisoformat(last)
            diff = (now - last_time).total_seconds()
            if diff < 3600:
                remaining = int(3600 - diff)
                minutes = remaining // 60
                seconds = remaining % 60
                return await interaction.response.send_message(
                    f"⏳ You must wait **{minutes}m {seconds}s** before working again."
                )

        jobs = [
                ("☕ Barista", (30, 60)),
                ("🧹 Janitor", (20, 50)),
                ("💻 Programmer", (70, 150)),
                ("🚚 Delivery Driver", (40, 90)),
                ("💼 Business Analyst", (100, 180)),
                ("🧪 Scientist", (150, 250)),
                ("🍔 Fast Food Worker", (25, 55)),
                ("📦 Warehouse Packer", (35, 70)),
                ("🛒 Store Cashier", (30, 65)),
                ("📮 Mail Sorter", (28, 60)),
                ("🚜 Farmhand", (35, 75)),
                ("🧰 Mechanic Assistant", (40, 80)),
                ("📚 Librarian", (45, 85)),
                ("🎨 Artist", (50, 100)),
                ("📝 Copywriter", (55, 110)),
                ("📞 Call Center Agent", (45, 95)),
                ("🔧 Technician", (60, 120)),
                ("🛠️ Repair Specialist", (70, 140)),
                ("🍕 Pizza Cook", (30, 65)),
                ("🏗️ Construction Worker", (60, 130)),
                ("🍽️ Waiter", (35, 70)),
                ("🚇 Subway Operator", (80, 150)),
                ("🧑‍🏫 Teacher", (60, 120)),
                ("🏥 Nurse Assistant", (70, 130)),
                ("👮 Security Guard", (55, 100)),
                ("🎥 Videographer", (75, 140)),
                ("📸 Photographer", (70, 130)),
                ("📦 Delivery Cyclist", (30, 65)),
                ("✏️ Graphic Designer", (70, 140)),
                ("🎧 Sound Technician", (75, 150)),
                ("🎤 Singer", (60, 130)),
                ("🎭 Actor", (50, 120)),
                ("🪚 Carpenter", (60, 130)),
                ("🧱 Bricklayer", (55, 115)),
                ("🧯 Firefighter", (90, 160)),
                ("🚑 Paramedic", (95, 170)),
                ("👩‍⚕️ Doctor Assistant", (120, 200)),
                ("🐶 Dog Walker", (25, 55)),
                ("🐱 Pet Groomer", (35, 75)),
                ("🧳 Hotel Porter", (40, 80)),
                ("🧼 Housekeeper", (35, 70)),
                ("🪑 Furniture Mover", (45, 90)),
                ("🛠️ Electrician", (80, 150)),
                ("🪜 Roofer", (75, 140)),
                ("🧯 Fire Inspector", (100, 180)),
                ("🛰️ Drone Operator", (90, 170)),
                ("🛠️ Robotics Technician", (120, 220)),
                ("🧬 Genetic Lab Assistant", (130, 230)),
                ("🏦 Bank Teller", (60, 110)),
                ("📊 Accountant", (80, 160)),
                ("📈 Stock Analyst", (120, 210)),
                ("💰 Loan Officer", (100, 180)),
                ("📢 Marketing Specialist", (70, 140)),
                ("📦 Logistics Coordinator", (75, 145)),
                ("🎮 Game Tester", (40, 90)),
                ("🎮 Game Developer", (100, 200)),
                ("🕹️ eSports Player", (80, 170)),
                ("📻 Radio Host", (75, 145)),
                ("📺 TV Reporter", (85, 160)),
                ("🎤 Podcast Host", (65, 130)),
                ("🧙 Wizard’s Apprentice", (50, 150)),
                ("⚒️ Blacksmith", (80, 170)),
                ("🧵 Tailor", (40, 90)),
                ("👗 Fashion Designer", (70, 150)),
                ("💇 Hair Stylist", (45, 100)),
                ("💅 Nail Artist", (40, 95)),
                ("🚤 Ferry Operator", (70, 135)),
                ("⛵ Sailor", (80, 150)),
                ("⚓ Dock Worker", (50, 100)),
                ("✈️ Flight Attendant", (90, 170)),
                ("🛫 Pilot (small aircraft)", (130, 220)),
                ("🛰️ Satellite Technician", (140, 260)),
                ("🧪 Chemist", (120, 210)),
                ("🧫 Lab Researcher", (130, 230)),
                ("🩺 Surgeon Assistant", (150, 260)),
                ("🤖 AI Engineer", (160, 280)),
                ("🧠 Neuroscientist", (170, 290)),
                ("🏛️ Lawyer", (140, 250)),
                ("📜 Judge Clerk", (100, 190)),
                ("🗂️ Office Manager", (70, 140)),
                ("📈 Financial Advisor", (130, 220)),
                ("🤝 HR Specialist", (65, 130)),
                ("🧮 Data Entry Clerk", (45, 85)),
                ("🛰️ Spaceport Technician", (140, 260)),
                ("🚀 Rocket Fuel Handler", (120, 220)),
                ("👨‍🚀 Astronaut Trainee", (180, 300)),
                ("🌋 Volcano Researcher", (130, 240)),
                ("🦈 Marine Biologist", (120, 210)),
                ("🌌 Astrophysicist", (170, 300)),
                ("🪐 Planetary Cartographer", (150, 260)),
                ("⚙️ Quantum Engineer", (200, 320)),
                ("🔮 Oracle Consultant", (180, 300)),
                ("🧛 Night Shift Guard", (60, 130)),
                ("🐉 Dragon Keeper", (150, 260)),
                ("💎 Treasure Appraiser", (130, 240)),
                ("🗺️ Expedition Leader", (160, 270)),
                ("🏰 Castle Steward", (110, 200)),
                ("⚔️ Monster Hunter", (140, 260)),
                ("🛡️ Royal Guard", (150, 240)),
                ("💫 Dimensional Explorer", (200, 340)),
                ("🌠 Starship Captain", (250, 380)),
                ("⚛️ Particle Researcher", (230, 360))
        ]

        job, pay_range = random.choice(jobs)
        reward = random.randint(*pay_range)


        if random.random() < 0.05:
            reward *= 3
            promo = " 🎉 **PROMOTION BONUS!**"
        else:
            promo = ""

        user["last_work"] = now.isoformat()
        await update_balance(uid, reward)
        save_state()

        await interaction.response.send_message(
            f"{job}: You earned **{reward} horsenncy!**{promo}"
        )
    @app_commands.command(name="shop", description="View the item shop & buy some desctructive things.")
    async def shop(self, interaction: discord.Interaction):
        items = state.get("items", {})

        if not items:
            return await interaction.response.send_message("🛒 The shop is empty. Come back later.")

        lines = []
        for item_id, item in items.items():
            lines.append(f"**{item['name']}** — {item['price']} horsenncy\n`{item_id}`")

        await interaction.response.send_message(
            "🛍️ **Shop Items**\n\n" + "\n".join(lines)
        )
    @app_commands.command(name="buy", description="Buy an item from the shop.")
    async def buy(self, interaction: discord.Interaction, item_id: str):
        import asyncio

        await interaction.response.defer()

        uid = interaction.user.id
        user = get_user(uid)
        items = state.get("items", {})

        if item_id not in items:
            return await interaction.followup.send("❌ Unknown item ID.")

        item = items[item_id]
        price = item["price"]

        if user["balance"] < price:
            return await interaction.followup.send("❌ You're too broke for that.")

        user["balance"] -= price
        inv = user.setdefault("inventory", {})
        inv[item_id] = inv.get(item_id, 0) + 1
        save_state()

        base_frames = [
            "```\n📦\n```",
            "```\n 📦\n```",
            "```\n  📦\n```",
            "```\n 📦\n```",
            "```\n📦\n```",
            "```\n\n📦\n```",  
            "```\n📦\n\n```",  
            "```\n 📦\n```",
            "```\n  📦\n```",
            "```\n 📦\n```",
            "```\n📦\n```"
        ]

        frames = base_frames * 2

        msg = await interaction.followup.send("📦", wait=True)
        for frame in frames:
            await asyncio.sleep(0.18)
            await msg.edit(content=frame)

        reveal = (
            f"🎉 **The box opens!**\n"
            f"✨ You received: **{item['name']}**\n"
            f"📦 Added to your inventory.\n"
        )

        await asyncio.sleep(0.3)
        await msg.edit(content=reveal)

    @app_commands.command(name="inventory", description="View your inventory.")
    async def inventory(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        data = get_user(target.id)

        inv = data.get("inventory", {})

        if not inv:
            return await interaction.response.send_message(
                f"📦 **{target.display_name}** has no items. Better pay off your rent."
            )

        lines = []
        for item_id, count in inv.items():
            item = state["items"].get(item_id, {"name": item_id})
            lines.append(f"**{item['name']}** × {count}")

        await interaction.response.send_message(
            f"📦 **{target.display_name}'s Inventory**\n" + "\n".join(lines)
        )
    @app_commands.command(name="use", description="Use an item from your inventory.")
    async def use_item(self, interaction: discord.Interaction, item_id: str, target: discord.User = None):
        uid = interaction.user.id
        user = get_user(uid)

        inv = user.get("inventory", {})

        if item_id not in inv or inv[item_id] <= 0:
            return await interaction.response.send_message("❌ You don’t have that item.")

        item = state["items"].get(item_id)
        if not item:
            return await interaction.response.send_message("❌ Invalid item ID.")

        if item_id == "intercontinental_ballistic_missile":
            if not target:
                return await interaction.response.send_message("You must choose a target.")
            await interaction.response.send_message(
                f"💥 **{interaction.user.display_name} launched a missile at {target.display_name}!!!**\nhttps://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzF4a3E2MXc3cnR3ZnNzbHVzMWsyNWRkd28wa3FqZmQ0d2RubzJuYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XUFPGrX5Zis6Y/giphy.gif"
            )
            user["inventory"][item_id] -= 1

        elif item_id == "red_button":
            candidates = [
                uid for uid in state["users"].keys()
                if uid != str(interaction.user.id)
            ]

            chosen = random.choice(candidates) if candidates else str(interaction.user.id)
            chosen_user = get_user(int(chosen))

            stolen = min(2000, chosen_user["balance"])
            chosen_user["balance"] -= stolen
            user["balance"] += stolen

            await interaction.response.send_message(
                f"🔴 **{interaction.user.display_name} pressed the Red Button of Death!**\n"
                f"💰 Stole **{stolen} horsenncy** from <@{chosen}>!"
            )

            inv[item_id] -= 1

        elif item_id == "mysterious_potion":
            outcome = random.randint(1, 3)
            if outcome == 1:
                user["balance"] = 0
                msg = "☠️ The potion exploded. You lost **ALL** your horsenncy."
            elif outcome == 2:
                user["balance"] *= 2
                msg = "✨ Your horsenncy **doubled!**"
            else:
                user["balance"] *= 3
                msg = "💎 Your horsenncy **tripled!**"

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "roast_protection":
            until = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
            user["roast_protection_until"] = until.isoformat()

            await interaction.response.send_message(
                "🛡️ You are protected from being roasted for **3 hours**!"
            )
            inv[item_id] -= 1

        elif item_id == "odd_box":
            rewards = random.sample(list(state["items"].keys()), 2)

            for r in rewards:
                inv[r] = inv.get(r, 0) + 1

            await interaction.response.send_message(
                f"🎁 You opened an Interesting Box!\nYou received:\n"
                + "\n".join([f"- **{state['items'][r]['name']}**" for r in rewards])
            )

            inv[item_id] -= 1
            
        elif item_id == "quantum_marshmallow":
            reward = random.randint(0, 500)
            user["balance"] += reward
            await interaction.response.send_message(
                f"✨ You consumed the **Quantum Marshmallow** and temporarily existed in 14 dimensions.\n"
                f"You earned **{reward} horsenncy** from the experience."
            )
            inv[item_id] -= 1

        elif item_id == "time_bending_hourglass":
            for key in ["last_work", "fish_cooldown", "hunt_cooldown", "last_daily"]:
                ts = user.get(key)
                if ts:
                    try:
                        old = datetime.datetime.fromisoformat(ts)
                        new = old - (old - datetime.datetime.utcnow()) * 0.5
                        user[key] = new.isoformat()
                    except:
                        pass
            await interaction.response.send_message(
                "⏳ You flipped the **Time-Bending Hourglass**.\n"
                "Your cooldowns have been **reduced by 50%**!"
            )
            inv[item_id] -= 1

        elif item_id == "void_pebble":
            await interaction.response.send_message(
                random.choice([
                    "🌑 You threw the **Void Pebble**. It fell upward. That shouldn't happen.",
                    "🕳️ The pebble vanished forever. So did your hopes.",
                    "🔮 The pebble whispered… *\"nice throw\"*."
                ])
            )
            inv[item_id] -= 1

        elif item_id == "cursed_duck":
            candidates = [
                uid for uid in state["users"].keys()
                if uid != str(interaction.user.id)
            ]
            if candidates:
                chosen = random.choice(candidates)
                chosen_user = get_user(int(chosen))
                stolen = random.randint(0, 3000)
                chosen_user["balance"] -= stolen
                user["balance"] += stolen
                msg = f"🐤 The **Cursed Duck** screamed at <@{chosen}> and stole **{stolen} horsenncy** for you!"
            else:
                msg = "🐤 The Cursed Duck screamed at nobody. It felt awkward."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "pocket_dimension_seed":
            reward = random.randint(0, 5000)
            user["balance"] += reward
            await interaction.response.send_message(
                f"🌱 You planted the **Pocket Dimension Seed** and opened a tiny universe.\n"
                f"You looted **{reward} horsenncy** from inside."
            )
            inv[item_id] -= 1

        elif item_id == "ethereal_lantern":
            user["lantern_boost"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
            await interaction.response.send_message(
                "🕯️ The **Ethereal Lantern** glows.\nYour next gamble has **+20% winnings** for 1 hour!"
            )
            inv[item_id] -= 1

        elif item_id == "glitched_coin":
            outcome = random.choice(["good", "bad", "neutral"])
            if outcome == "good":
                gain = random.randint(10, 5000)
                user["balance"] += gain
                msg = f"💾 The Glitched Coin duplicated itself! You earned **{gain} horsenncy**!"
            elif outcome == "bad":
                loss = random.randint(10, 100000)
                user["balance"] -= loss
                msg = f"⚠️ The Glitched Coin corrupted! You lost **{loss} horsenncy**."
            else:
                msg = "🌀 The Glitched Coin flickered and did nothing. Nice."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "orb_of_unlikely_events":
            roll = random.randint(1, 3)
            if roll == 1:
                gain = random.randint(0, 10000)
                user["balance"] += gain
                msg = f"🔮 A miracle! You gained **{gain} horsenncy**!"
            elif roll == 2:
                loss = max(5000, user["balance"])
                user["balance"] -= loss
                msg = f"🐸 A frog materialized and stole **{loss} horsenncy**."
            else:
                msg = "⭐ Nothing happened. Statistically the rarest outcome?"

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "sentient_spoon":
            await interaction.response.send_message(
                "🥄 The Sentient Spoon whispers:\n**'stop using discord commands and touch grass.'**"
            )
            inv[item_id] -= 1

        elif item_id == "chaos_sandwich":
            mode = random.randint(1, 3)
            if mode == 1:
                user["balance"] = random.randint(0, 10000)
                msg = "🥪 Chaos Sandwich rewrote your timeline. Your balance is now *random*. Yum!"
            elif mode == 2:
                user["balance"] += 300
                msg = "🥪 The sandwich spit out 300 horsenncy. Yay!"
            else:
                loss = 5000
                user["balance"] = max(0, user["balance"] - loss)
                msg = f"🥪 The sandwich bit you. You dropped **{loss} horsenncy**."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "lurking_shadow_fragment":
            user["hunt_shadow_boost"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
            await interaction.response.send_message(
                "🌑 A shadow follows you now. Your next **hunt** has **+15% success**."
            )
            inv[item_id] -= 1

        elif item_id == "rainbow_thunder_crystal":
            gain = random.randint(0, 3000)
            user["balance"] += gain
            await interaction.response.send_message(
                f"🌈⚡ The crystal zaps you with pride energy.\nYou gained **{gain} horsenncy**!"
            )
            inv[item_id] -= 1

        elif item_id == "mechanical_gremlin":
            action = random.choice(["steal", "eat", "dance"])
            if action == "steal":
                candidates = [
                    uid for uid in state["users"].keys()
                    if uid != str(interaction.user.id)
                ]
                if candidates:
                    chosen = random.choice(candidates)
                    chosen_user = get_user(int(chosen))
                    stolen = max(chosen_user["balance"], 1500)
                    chosen_user["balance"] -= stolen
                    user["balance"] += stolen
                    msg = f"🤖 Your Mechanical Gremlin stole **{stolen} horsenncy** from <@{chosen}>!"
                else:
                    msg = "🤖 The Gremlin tried to steal but found nobody."

            elif action == "eat":
                loss = 1200
                user["balance"] = max(0, user["balance"] - loss)
                msg = f"🤖 The Gremlin malfunctioned and ate **{loss} horsenncy**."

            else:
                msg = "🤖 The Gremlin danced enthusiastically. No effect."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "antigravity_rubber_ducky":
            reward = random.randint(0, 1000)
            user["balance"] += reward
            await interaction.response.send_message(
                f"🦆✨ The Anti-Gravity Ducky floated away and dropped **{reward} horsenncy** for you."
            )
            inv[item_id] -= 1

        elif item_id == "forgotten_scroll":
            gain = random.randint(0, 3000)
            user["balance"] += gain
            await interaction.response.send_message(
                f"📜 You read the **Forgotten Scroll**.\nYou gained **{gain} horsenncy** because knowledge is power."
            )
            inv[item_id] -= 1

        elif item_id == "ancient_snack":
            roll = random.randint(1, 3)
            if roll == 1:
                gain = random.randint(0, 500)
                user["balance"] += gain
                msg = f"🍪 You ate the Ancient Snack. It tasted eternal. You earned **{gain} horsenncy**."
            elif roll == 2:
                user["balance"] = max(0, user["balance"] - 500)
                msg = "🍘 The snack turned to dust. You lost **500 horsenncy**."
            else:
                user["balance"] += 50
                msg = "🍪 Surprisingly tasty! You gained **50 horsenncy**."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "starlit_compass":
            user["fish_buff"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
            await interaction.response.send_message(
                "🧭 The **Starlit Compass** glows.\nYour next fishing reward is **doubled**!"
            )
            inv[item_id] -= 1

        elif item_id == "cryptic_cube":
            roll = random.randint(1, 3)
            if roll == 1:
                user["balance"] += 2000
                msg = "🧊 The Cube granted you **2000 horsenncy**."
            elif roll == 2:
                loss = 10000
                user["balance"] = max(0, user["balance"] - loss)
                msg = f"🧊 The Cube demanded tribute. You lost **{loss} horsenncy**."
            else:
                msg = "🧊 The Cube hums ominously. Nothing happens."

            await interaction.response.send_message(msg)
            inv[item_id] -= 1

        elif item_id == "cookie_unstable":
            await interaction.response.send_message(
                "🍪 You ate the **??? Cookie**. Everyone is uncomfy. Including you."
            )
            inv[item_id] -= 1

        elif item_id == "paradox_clock":
            user["paradox_buff"] = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).isoformat()
            await interaction.response.send_message(
                "⏰ Reality bends.\nYour next daily/work/battle gives **2× horsenncy**!"
            )
            inv[item_id] -= 1

        save_state()

async def setup(bot):
    print("Loading Economy Cog...")
    await bot.add_cog(Economy(bot))
    print("Economy Cog Loaded!")
