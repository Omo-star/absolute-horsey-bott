# FuSBot

A powerful, feature-packed Discord bot with advanced roast AI, a fully simulated economy, gambling games, dungeon crawler, stock market, hunting/fishing systems, and a personal codepad environment — all using **slash commands only**.

The name represent the goal of this bot, to be a fun, full-server bot that will help you out! The name stands for Full (Fu) Server (S) Robot (Bot).

---

## Activation

1. Invite the bot:  
   [FuSBot](https://discord.com/oauth2/authorize?client_id=1440004841559560214&scope=bot+applications.commands&permissions=2147483648)
2. Add it to all apps.
3. Use slash commands (`/`) to access all features.

---

# Command Index (With Detailed Descriptions)

---

# 🔥 1. Roast System

### `/roast text:"..."`  
Generates an AI-driven roast targeting any mentioned users.  
Supports:
- Multi-target roasting  
- Personal memory-based insults  
- Roast protection detection  
- Adjustable tone & intensity  

### `/data user:@User`  
Shows all roast-related stored data for a user, such as:
- Personality profile  
- Roasting history  
- Protection timers  

Auto-roast behavior automatically fires when users mention the bot.

---

# 📁 2. Codepad System

A fully isolated “mini workspace” stored per user.

### `/code_new filename`  
Creates a new file in your personal code directory.

### `/code_edit filename`  
Opens a modal to edit the file content.

### `/code_view filename`  
Displays the file’s full content in an embed.

### `/code_list`  
Shows all files you have created.

### `/code_delete filename`  
Deletes a file permanently.

### `/code_run filename`  
Executes the file in a safe sandbox environment and returns the output.

Great for small scripts, notes, templates, or meme code.

---

# 💰 3. Economy System (horsenncy)

## Core Currency Actions

### `/balance [user]`  
View your own or another user’s horsenncy balance.

### `/daily`  
Claim a random daily reward (100–300 horsenncy). 24h cooldown.

### `/work`  
Perform one of 100+ possible jobs with varying payment.  
Includes:
- Promotions  
- Pay range scaling  
- 1 hour cooldown  
- Chance of triple pay bonuses  

### `/give user amount`  
Transfer horsenncy to another user.

### `/pray`  
Pray to Horsey. Grants a prayer point which boosts:
- Gambling win multipliers  
- Crime/luck modifiers  
- Dungeon bonuses  
10% chance to *reset your prayer points to zero.*

### `/leaderboard`  
Shows the top 10 wealthiest players.

---

# 🎲 4. Gambling Suite

### `/blackjack bet`  
Full interactive Blackjack:
- Animated ASCII-style cards  
- Hit/Stand  
- Dynamic dealer logic  
- Prayer boost applies  
- Proper Ace logic  

### `/slots bet`  
3×3 slot machine with:
- Multi-line wins  
- Rows, columns, diagonals  
- Mythic jackpots & god events  
- Animated reveal sequence  

### `/coinflip side amount`  
50/50 gamble.  
Prayer boost affects winnings.  
Heads or tails.

### `/crime`  
Commit crimes with varying payout.  
Includes:
- High-risk heists  
- Legendary multipliers  
- Rare 10× jackpots  
- Serious failures (police can wipe all your money)

---

# 🦌 5. Hunting System — `/hunt`

Go hunting and catch one of over **130+ creatures**, ranging from:
- Common wildlife  
- Rare beasts  
- Mythic monsters  
- Dragons, phoenixes, cosmic entities  

Features:
- Weighted rarities  
- Critical hits  
- Prayer-based reward scaling  
- Escape mechanics  
- Loot added to your Owned Animals

---

# 🎣 6. Fishing System — `/fish`

Similar to hunting but with **fish, sea monsters, leviathans, and cosmic aquatic creatures**.

Features:
- Rod break chance  
- Weighted fishing table  
- Jackpot catches  
- Prayer buffs  
- Mythic sea creatures  
- Doubled rewards from special items

---

# ⚔️ 7. Battle System — `/battle`

Fight one of 150+ monsters with:
- Base win rates  
- Team bonuses  
- Prayer multipliers  
- Critical strikes  
- Huge boss variants (World Eater, Titans, Dragons)

If you win:
- Earn horsenncy based on monster difficulty  
If you lose:
- Drop horsenncy

---

# 🐾 8. Animals & Team System — `/team`

Your hunted creatures can join your battle team.

### `/team list`  
Shows all owned animals grouped by type, rarity, and strength.

### `/team add index`  
Adds an owned animal to your battle team (max 8).

### `/team remove index`  
Removes an animal from your battle team.

Team strength increases battle win chance.

---

# 🏛️ 9. Stock Market System

### `/stocks`  
Opens the live Horsey Stock Exchange dashboard:
- Real-time simulated price changes  
- Market-wide events  
- Symbol-specific news  
- Random volatility  
- Personal portfolio display  

### `/stocks_buy SYMBOL AMOUNT`  
Purchase shares based on current price.

### `/stocks_sell SYMBOL AMOUNT`  
Sell shares to earn horsenncy.

The market fluctuates constantly — check `/stocks` often.

---

# 🏰 10. Dungeon System — `/dungeon`

A full RPG dungeon crawler with dozens of mechanics.

### CORE FEATURES
- Floor exploration  
- Ambient events & traps  
- Sanity mechanics  
- Energy system  
- Mutations  
- Curses  
- Relics  
- Global raid boss  
- Rift instability  
- Skill point allocation  
- Randomized loot & enemies  
- PvP dungeon invasions  
- Rift dives  
- Final cash-out rewards  

### BUTTON ACTIONS
- **Explore** — Fights, loot, relics, traps, shrines  
- **Rest** — Heal or be ambushed  
- **Skills** — Level up Might, Ward, Greed, Warp, Instinct  
- **Raid Boss** — Contribute damage to the world boss  
- **Rift Dive** — Extremely dangerous but high-reward  
- **Leave** — End your run and earn horsenncy  

Runs are tracked permanently.

---

# 🛍️ 11. Shop & Items

### `/shop`  
View all available items.

### `/buy item_id`  
Purchase an item by its ID.

### `/inventory [user]`  
View your own or another user’s items.

### `/use item_id [target]`  
Use an item — effects vary dramatically.

Item categories:
- Explosive items (missiles)
- RNG chaos artifacts  
- Currency modifiers  
- Time manipulation items  
- Dungeon modifiers  
- Red Button (steals from random user)  
- Gremlins, cursed ducks, orbs, void objects  
- Buffs to hunt/fish/battle/work/daily  

Over **30+ items**, each with entirely custom logic.

---

# 🤖 12. Lichess Bot

**User: [@icbmsaregoated2](https://lichess.org/@/icbmsaregoated2)**
### '/lichess'

View current status of lichess bot on a user-friendly dashbored.

### '/lichess_game'

View current moves of the game it is playing.

**Example statistics**

- Current rating
- Time control
- Variant
- Opponent rating

---

# 🌀 13. Voidmaze System — `/voidmaze`

A cosmic, sanity-bending roguelite where every choice reshapes both **you** and the **Maze**.

### CORE FEATURES
- Depth-based progression  
- Clarity (HP) system with degrading thresholds  
- Artifacts with powerful combo synergies  
- Anomalies that corrupt and hinder your run  
- Boons granting rare buffs  
- Fragments, keys, and combo chaining  
- Procedurally generated rooms  
- Global world-state variables (Storm, Pulse, Season)  
- Seasonal shifts that alter Maze behavior  
- Passive synergy engine that triggers automatically  
- High-risk collapse events that can delete horsenncy  
- Run history, best depth, streak tracking  

---

### ROOM TYPES
- **Door of the Abyss** — Gain depth & fragments; lose clarity; anomaly chance  
- **Tangle Key Node** — Puzzle granting keys, clarity, or anomalies  
- **Artifact Vault** — Earn artifacts with scaling power; may backlash  
- **Reality Fracture** — Extremely high risk; artifacts, wealth, anomalies, or instant collapse  
- **Locus of Stillness** — Restore clarity or be ambushed  
- **Echo Storm** — Alters world-state (Storm, Pulse, Season)  

---

### BUTTON ACTIONS
- **Room 1 / Room 2 / Room 3** — Choose one of three procedurally generated events  
- **Leave Maze** — End the run and convert progress into horsenncy  

Rewards depend on:  
Depth, artifacts, anomalies, fragments, keys, combo streak, and world-state conditions.

---

# 🏟️ 14. Arena System — `/arena`

A fast-paced **auto-battler arena** where your animals fight through elemental matchups, ultimates, passives, and seasonal modifiers.

### CORE FEATURES
- Auto-battler combat with full stat generation  
- Elements, roles, rarities, crits, shields, and speed ordering  
- Ultimate abilities for every element  
- Status effects: burn, poison, bleed, stun, regen  
- Environment cycles that boost/nerf certain elements  
- Global Arena Seasons & Chaos meter  
- Match Mutators (Bloodsport, Iron Wall, Arcane Storm, etc.)  
- Win streak rewards & evolution system  
- Permanent passive upgrades via Crown Shop  
- Rating ladder with top-10 leaderboard  
- Daily fight tokens (3 per day)

---

### WHAT YOU CAN DO
- **Fight Match** — Enter a full auto-battle with animations, abilities, and ultimates  
- **Edit Team** — Choose up to 5 animals from your Owned Animals  
- **View Ladder** — See global top ratings  
- **Crown Shop** — Buy permanent Arena buffs  
- **Leave Arena** — Exit the lobby

---

### BATTLE SYSTEM
Each fighter is assigned:
- **Element** (fire, water, air, earth, dark, mystic, beast)  
- **Role** (tank, striker, support, healer, trickster)  
- **Rarity** (Common → Legendary)  
- **Unique passive ability**  
- **Randomized combat stats:** HP, Power, Defense, Speed, Crit Rate

Combat includes:
- Type advantages  
- Shields, buffs, debuffs  
- DOTs (burn/poison/bleed)  
- Momentum boosts  
- Round-end passives (heals, speed auras, etc.)  
- Full team synergy bonuses  

---

### EVOLUTIONS
Win streaks evolve animals into stronger forms (Wolf → Dire Wolf → Moon Wolf, etc.).  
Evolutioned units replace the older form in future teams.

---

### REWARDS
Match results give:
- **Rating** (MMR)  
- **XP** (leveling → crowns)  
- **Crowns** (permanent upgrades)  
- **Streak bonuses**  
- **Seasonal world progression**

---

### SUMMARY
The Arena is a **deep auto-battler** combining:
- Team building  
- Synergies  
- RNG chaos  
- Strategic passives  
- Seasonal meta shifts  

Master your squad, climb the ladder, and become the Arena Champion.

---

# 🧪 15. Research Lab System — `/lab`

A high-risk, high-reward **scientific progression system** where stability, anomalies, breakthroughs, and world instability shape your research journey.

### CORE FEATURES
- Lab leveling & XP system  
- Stability & max-stability management  
- Global instability meter  
- Random anomalies with escalating danger  
- Breakthroughs that permanently enhance your account  
- Research, experiments, and stabilization cycles  
- Lab world events shared across all players  
- Risk-based horsenncy experiments  
- Chance-based breakthrough unlock table  
- Persistent logs & research queue

---

### BUTTON ACTIONS
- **Research** — Gain XP, raise instability, reduce stability, chance for breakthroughs  
- **Experiment** — Gamble horsenncy with high variance; can yield XP, anomalies, or catastrophes  
- **Stabilize** — Spend lab XP to restore stability, reduce world instability, and sometimes purge anomalies  
- **Breakthroughs** — View all permanent upgrades unlocked  
- **Leave** — Exit the lab interface

---

### SYSTEM MECHANICS

#### **Stability**
- Core safety meter: if it hits zero → **Core Fracture** anomaly  
- Experiments & research reduce stability  
- Stabilization restores stability and may remove anomalies

#### **Instability (World)**
- Shared across labs globally  
- Rises with research & experiments  
- High levels increase breakthrough rates and catastrophe odds  
- Certain thresholds trigger world events

#### **Breakthroughs**
Unique permanent upgrades such as:
- Efficient Stock Algos  
- Dungeon Resonance Mapping  
- Arena Combat Analytics  
- Prayer Wave Amplifier  
- Casino Edge Tuning  
- Meta-Currency Compression  

Each breakthrough adds flavor, future upgrades, or system synergies.

#### **Experiments**
Outcome tiers:
- **Major Success** — High horsenncy gain + XP, major instability spike  
- **Minor Success** — Small net gain, mild instability  
- **Failure** — Horsenncy loss + new anomaly  
- **Catastrophic Failure** — Huge loss, stability crash, severe anomaly

---

### SUMMARY
The Research Lab is a **progression + risk management system** built around:
- XP growth  
- Stability juggling  
- Random anomalies  
- Permanent breakthroughs  
- Horsenncy wagers  
- A global evolving instability field  

Master the lab, tame the anomalies, and advance scientific chaos.

---

# 🛠️ 16. Hacker RPG System — `/hack`

A fully simulated **multi-phase hacking RPG** powered by your **own codepad scripts**.  
Every hack evaluates your scripts for performance, efficiency, stealth, stability, and complexity — creating a deeply customizable cyber-RPG loop.

---

### CORE FEATURES
- Four-phase hacking chain: **Recon → Access → Payload → Extraction**  
- Script analysis engine (performance, entropy, recursion, imports, stealth, parallelism, stability)  
- Automatic module selection or manual script assignment  
- Difficulty tiers (1–5) with unique target security profiles  
- Skill, Tier, Reputation, Trace, and XP progression  
- Success quality grading (flawless, barely, almost, failed)  
- Synergy bonuses for archetype alignment or diversity  
- Animated phase-by-phase hack visualization  
- Cooldowns that adapt to skill, tier, and trace  
- Persistent hack history (20 most recent runs stored)

---

### BUTTONLESS SYSTEM  
All actions occur through the `/hack` command and your **codepad**.

### HOW IT WORKS
1. Create code files using `/code_new` and `/code_edit`.  
2. Name them according to role keywords:  
   - **Recon** — recon, scan, probe  
   - **Access** — access, login, auth  
   - **Payload** — payload, inject, exploit  
   - **Extraction** — extract, exfil, leak  
3. Run `/hack` and optionally specify which scripts to use.  
4. Watch the engine analyze your code and simulate a cyber intrusion.

---

### PHASES
- **Reconnaissance** — Mapping endpoints, fingerprinting, topology analysis  
- **Access Vector** — Credential distortion, solver heuristics, exploit probes  
- **Payload Orchestration** — Packing, obfuscation, execution hooks  
- **Extraction** — Proxy braiding, masking envelopes, sealing channels  

Each phase compares:  
**your script power** vs **target threshold**, modified by skill, tier, trace, and synergy.

---

### OUTCOME TYPES
- **Perfect Chain** — Stunning execution; massive XP & stat boosts  
- **Strong** — Solid multi-phase breach  
- **Clean** — Consistent success  
- **Shaky** — Success with instability  
- **Near Miss** — Almost broke in  
- **Messy** — Failed with noise  
- **Catastrophic** — Severe failure; high trace

---

### PROGRESSION
Hacks reward or penalize:
- **XP** (skill-up & tier progression)  
- **Skill** (hack power scaling)  
- **Reputation** (public notoriety)  
- **Trace** (forensic heat)  
- **Streaks** (bonus consistency multiplier)

Trace also increases cooldown time.

---

### CHAIN BUILDING
During execution:
- System animates each phase  
- Evaluates module matchups  
- Calculates margin %, quality, synergy, RNG volatility  
- Produces a detailed final report

---

### SUMMARY
The `/hack` system is a **deep technical RPG** where:
- Your scripts = your equipment  
- Your skill & tier = your stats  
- Trace = your danger meter  
- Each target = a unique puzzle

Build better scripts, form strong phase chains, and climb the hacker ranks.

---

# End

**Thank you for reading :) Hope you enjoy the bot!**
