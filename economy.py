# beta owo-bot esque feature!

import discord
from discord.ext import commands
from discord import app_commands
import datetime
import random
import json, os

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"users": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
state = load_state()
def get_user(uid: int):
    uid = str(uid)
    if uid not in state["users"]:
        state["users"][uid] = {
            "balance": 0,
            "last_daily": None
        }
        save_state(state)
        state = load_state()
    return state["users"][uid]


async def get_balance(user_id: int) -> int:
    return get_user(user_id)["balance"]


async def update_balance(user_id: int, amount: int):
    user = get_user(user_id)
    user["balance"] += amount
    save_state(state)


async def set_daily_timestamp(user_id: int):
    user = get_user(user_id)
    user["last_daily"] = datetime.datetime.utcnow().isoformat()
    save_state(state)


async def get_last_daily(user_id: int):
    return get_user(user_id)["last_daily"]


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

            member = interaction.guild.get_member(uid_int)
            name = member.display_name if member else f"User {uid}"

            lines.append(f"**#{rank}** — {name}: **{balance} coins**")
            rank += 1

        await interaction.response.send_message(
            "🏆| **Top 10 Richest Users**\n" + "\n".join(lines)
        )


async def setup(bot):
    await bot.add_cog(Economy(bot))
