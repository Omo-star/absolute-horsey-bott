# beta owo-bot esque feature!

import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import datetime
import random

DB_NAME = "economy.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL,
                last_daily TEXT
            );
        """)
        await db.commit()

async def get_balance(user_id: int) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, balance, last_daily) VALUES (?, ?, ?)",
                (user_id, 0, None),
            )
            await db.commit()
            return 0
        return row[0]

async def update_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, balance, last_daily)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET balance = balance + excluded.balance
            """,
            (user_id, amount, None),
        )
        await db.commit()

async def set_daily_timestamp(user_id: int):
    now = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET last_daily = ? WHERE user_id = ?", (now, user_id)
        )
        await db.commit()

async def get_last_daily(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT last_daily FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your coin balance.")
    async def balance(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        coins = await get_balance(target.id)
        await interaction.response.send_message(
            f"💰 **{target.display_name}** has **{coins} coins**."
        )

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
            f"🎁 **Daily Reward:** You received **{reward} coins!**"
        )

    @app_commands.command(name="give", description="Give coins to another user.")
    async def give(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.")
            return

        sender = interaction.user
        sender_balance = await get_balance(sender.id)

        if sender.id == user.id:
            await interaction.response.send_message("You cannot give coins to yourself.")
            return

        if sender_balance < amount:
            await interaction.response.send_message("You don't have enough coins.")
            return

        await update_balance(sender.id, -amount)
        await update_balance(user.id, amount)
        await interaction.response.send_message(
            f"🤝 {sender.display_name} gave **{amount} coins** to {user.display_name}!"
        )

    @app_commands.command(name="coinflip", description="Bet coins on a coin flip.")
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
            await interaction.response.send_message("You don't have enough coins.")
            return

        result = random.choice(["heads", "tails"])
        win = result == side

        if win:
            await update_balance(uid, amount)
            await interaction.response.send_message(
                f"🎉 The coin landed on **{result}** — you won **{amount} coins!**"
            )
        else:
            await update_balance(uid, -amount)
            await interaction.response.send_message(
                f"💀 The coin landed on **{result}** — you lost **{amount} coins.**"
            )

    @app_commands.command(name="leaderboard", description="Top players by coins.")
    async def leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_NAME) as db:
            cur = await db.execute(
                "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10"
            )
            rows = await cur.fetchall()

        if not rows:
            await interaction.response.send_message("No data yet.")
            return

        lines = []
        rank = 1
        for user_id, balance in rows:
            user = interaction.guild.get_member(user_id)
            name = user.display_name if user else f"User {user_id}"
            lines.append(f"**#{rank}** — {name}: **{balance} coins**")
            rank += 1

        await interaction.response.send_message(
            "🏆 **Top 10 Richest Users**\n" + "\n".join(lines)
        )

async def setup(bot):
    await init_db()
    await bot.add_cog(Economy(bot))
