from economy_shared import state, save_state
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
import tempfile
import os

def sandbox_exec(code: str):
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

async def run_cpp(code: str) -> str:
    tmpdir = tempfile.mkdtemp(prefix="codepad_cpp_")
    src_path = os.path.join(tmpdir, "main.cpp")
    bin_path = os.path.join(tmpdir, "main.out")

    try:
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            proc = await asyncio.create_subprocess_exec(
                "g++",
                src_path,
                "-O2",
                "-std=c++17",
                "-o",
                bin_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return "g++ compiler not found on this system."

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
        except asyncio.TimeoutError:
            proc.kill()
            return "Compilation timed out."

        if proc.returncode != 0:
            err = stderr.decode(errors="ignore")
            if not err.strip():
                err = "Unknown compilation error."
            return "Compilation failed:\n" + err

        try:
            run_proc = await asyncio.create_subprocess_exec(
                bin_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return "Compiled binary missing after build."

        try:
            rstdout, rstderr = await asyncio.wait_for(run_proc.communicate(), timeout=3)
        except asyncio.TimeoutError:
            run_proc.kill()
            return "Program execution timed out."

        out = ""
        if rstdout:
            out += rstdout.decode(errors="ignore")
        if rstderr:
            if out:
                out += "\n"
            out += "stderr:\n" + rstderr.decode(errors="ignore")

        if not out.strip():
            out = "(no output)"

        return out
    finally:
        try:
            if os.path.exists(src_path):
                os.remove(src_path)
        except Exception:
            pass
        try:
            if os.path.exists(bin_path):
                os.remove(bin_path)
        except Exception:
            pass
        try:
            if os.path.isdir(tmpdir):
                os.rmdir(tmpdir)
        except Exception:
            pass

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

    @app_commands.command(name="code_run", description="Run a code file (Python or C++).")
    async def code_run(self, interaction: discord.Interaction, filename: str):
        pad = self.get_user_pad(interaction.user.id)

        if filename not in pad:
            return await interaction.response.send_message("❌ File does not exist.")

        code = pad[filename]

        if not code.strip():
            return await interaction.response.send_message("❌ File is empty.")

        await interaction.response.defer()

        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        if ext in ("cpp", "cc", "cxx"):
            output = await run_cpp(code)
        else:
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
