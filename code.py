from economy import state, save_state
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import traceback
import math
import random
import statistics
import itertools

def sandbox_exec(code: str):
    # runs python code, which may or may not be risky. who cares anyway tbh
    
    # allowed commands
    allowed_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "math": math,
        "random": random,
        "statistics": statistics,
        "stats": statistics,
        "itertools": itertools
    }

    env = {
        "__builtins__": allowed_builtins
    }

    output = []

    def fake_print(*args):
        output.append(" ".join(str(a) for a in args))

    env["print"] = fake_print

    try:
        exec(code, env, env)
    except Exception as e:
        output.append("Error: " + str(e))
        tb = traceback.format_exc()
        output.append(tb)

    return "\n".join(output)

class CodeEditModal(discord.ui.Modal, title="Edit Code File"):
    filename: str

    def __init__(self, filename, original):
        super().__init__()
        self.filename = filename

        self.code = discord.ui.TextInput(
            label=f"Editing {filename}",
            style=discord.TextStyle.long,
            default=original,
            max_length=4000
        )
        self.add_item(self.code)

    async def on_submit(self, interaction: discord.Interaction):
        pad = interaction.client.get_cog("Codepad").get_user_pad(interaction.user.id)
        pad[self.filename] = self.code.value
        save_state()
        await interaction.response.send_message(f"✏️ Updated **{self.filename}**.")

class Codepad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_user_pad(self, user_id):
        uid = str(user_id)
        if "codepad" not in state:
            state["codepad"] = {}
        if uid not in state["codepad"]:
            state["codepad"][uid] = {}
            save_state()
        return state["codepad"][uid]

    @app_commands.command(name="code_new", description="Create a new code file.")
    async def code_new(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename in pad:
            return await interaction.response.send_message("❌ File already exists.")

        pad[filename] = ""
        save_state()

        await interaction.response.send_message(f"📄 Created file **{filename}**.")

    @app_commands.command(name="code_edit", description="Edit code in a popup editor.")
    async def code_edit(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename not in pad:
            return await interaction.response.send_message("❌ File does not exist.")

        modal = CodeEditModal(filename, pad[filename])
        await interaction.response.send_modal(modal)


    @app_commands.command(name="code_view", description="View code in a file.")
    async def code_view(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename not in pad:
            return await interaction.response.send_message("❌ File does not exist.")

        code = pad[filename]
        if not code:
            code = "(empty file)"

        await interaction.response.send_message(
            f"📄 **{filename}**:\n```py\n{code}\n```"
        )

    @app_commands.command(name="code_list", description="List all your code files.")
    async def code_list(self, interaction: discord.Interaction):
        pad = self.get_user_pad(interaction.user.id)

        if not pad:
            return await interaction.response.send_message("📂 You have no files.")

        lines = "\n".join(f"- {fn}" for fn in pad.keys())
        await interaction.response.send_message(
            "📂 **Your Files:**\n" + lines
        )

    @app_commands.command(name="code_delete", description="Delete a code file.")
    async def code_delete(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename not in pad:
            return await interaction.response.send_message("❌ File does not exist.")

        del pad[filename]
        save_state()

        await interaction.response.send_message(f"🗑️ Deleted **{filename}**.")

    @app_commands.command(name="code_run", description="Run a code file safely.")
    async def code_run(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename not in pad:
            return await interaction.response.send_message("❌ File does not exist.")

        code = pad[filename]

        if not code.strip():
            return await interaction.response.send_message("❌ File is empty.")

        await interaction.response.defer()

        output = sandbox_exec(code)

        if len(output) > 1900:
            output = output[:1900] + "\n...<truncated>"

        embed = discord.Embed(
            title=f"📟 Output of {filename}",
            description=f"```txt\n{output}\n```",
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Codepad(bot))
