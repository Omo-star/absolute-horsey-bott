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

**User: [@icbmsaregoated2](https://lichess.org/@/icbmsaregoated2)
### '/lichess'

View current status of lichess bot

### '/lichess_game'

View current moves of the game it is playing

**Example statistics**

- Current rating
- Time control
- Variant
- Opponent rating

---

# Notes

- All systems use persistent storage.
- Some systems (Raid Boss, Rift Instability) are **global** and affect all players.
- Many mechanics interact with each other (e.g., prayer boosts gambling and dungeon, items boost hunting or fish rewards).

---

# End

**Thank you for reading :) Hope you enjoy the bot!**
