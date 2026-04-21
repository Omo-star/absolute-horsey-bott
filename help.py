import datetime
import discord
from discord.ext import commands
from discord import app_commands


TOPIC_ALIASES = {
    "start": "start",
    "beginner": "start",
    "new": "start",
    "getting started": "start",
    "getting-started": "start",
    "economy": "economy",
    "money": "economy",
    "cash": "economy",
    "adventure": "adventure",
    "games": "adventure",
    "combat": "adventure",
    "grind": "adventure",
    "deep": "deep",
    "systems": "deep",
    "ai": "ai",
    "roast": "ai",
    "code": "ai",
    "hack": "ai",
    "admin": "admin",
    "setup": "admin",
    "mod": "admin",
    "moderation": "admin",
    "fun": "fun",
    "misc": "fun",
    "extras": "fun",
    "all": "all",
}


def normalize_topic(topic: str | None) -> str:
    text = (topic or "start").strip().lower()
    return TOPIC_ALIASES.get(text, "start")


def make_embed(topic: str, user: discord.abc.User):
    topic = normalize_topic(topic)

    if topic == "economy":
        embed = discord.Embed(
            title="💰 help • economy",
            description="money, items, stocks, trading, and progression basics",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Core Money",
            value=(
                "`/balance` see your horsenncy\n"
                "`/daily` claim free money\n"
                "`/work` do jobs\n"
                "`/give` send money to someone\n"
                "`/pray` gain prayer points\n"
                "`/leaderboard` richest players"
            ),
            inline=False
        )
        embed.add_field(
            name="Risk and Gambling",
            value=(
                "`/blackjack`\n"
                "`/coinflip`\n"
                "`/crime`\n"
                "`/slots`"
            ),
            inline=False
        )
        embed.add_field(
            name="Items, Market, and Player Trading",
            value=(
                "`/shop`\n"
                "`/buy`\n"
                "`/inventory`\n"
                "`/use`\n"
                "`/stocks`\n"
                "`/stocks_buy`\n"
                "`/stocks_sell`\n"
                "`/auction browse`\n"
                "`/auction sell`\n"
                "`/auction buy`"
            ),
            inline=False
        )
        embed.set_footer(text="easy starter route: /daily → /work → /shop or /stocks")
        return embed

    if topic == "adventure":
        embed = discord.Embed(
            title="⚔️ help • adventure",
            description="creatures, teams, combat, and your core grinding routes",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Creature Loop",
            value=(
                "`/hunt` get creatures\n"
                "`/fish` get fish and sea monsters\n"
                "`/team list` see your team\n"
                "`/team add` add a creature\n"
                "`/team remove` remove one\n"
                "`/battle` fight monsters"
            ),
            inline=False
        )
        embed.add_field(
            name="Big Progression Modes",
            value=(
                "`/dungeon` evolving dungeon run\n"
                "`/voidmaze` cosmic roguelite\n"
                "`/arena` auto-battler ladder\n"
                "`/lab` research lab"
            ),
            inline=False
        )
        embed.add_field(
            name="Account and Progress Tracking",
            value=(
                "`/profile`\n"
                "`/achievements`\n"
                "`/quests`\n"
                "`/titles`\n"
                "`/collections`"
            ),
            inline=False
        )
        embed.set_footer(text="easy starter route: /hunt or /fish → /team list → /battle → /dungeon")
        return embed

    if topic == "deep":
        embed = discord.Embed(
            title="🌀 help • deep systems",
            description="the heavier systems once you want more than quick commands",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Account Layer",
            value=(
                "`/profile` overview\n"
                "`/achievements` unlock board\n"
                "`/quests` daily goals\n"
                "`/quests_claim` claim rewards\n"
                "`/titles` unlocked titles\n"
                "`/title_equip` equip a title\n"
                "`/collections` account-wide collection progress"
            ),
            inline=False
        )
        embed.add_field(
            name="Social Layer",
            value=(
                "`/guild create`\n"
                "`/guild join`\n"
                "`/guild leave`\n"
                "`/guild info`\n"
                "`/guild deposit`\n"
                "`/guild upgrade`"
            ),
            inline=False
        )
        embed.add_field(
            name="High-Depth Modes",
            value=(
                "`/dungeon`\n"
                "`/voidmaze`\n"
                "`/arena`\n"
                "`/lab`\n"
                "`/hack`"
            ),
            inline=False
        )
        embed.set_footer(text="this is the layer that ties the rest of the bot together")
        return embed

    if topic == "ai":
        embed = discord.Embed(
            title="🤖 help • ai and utility",
            description="roast ai, codepad, hacking, images, and lichess",
            color=discord.Color.teal(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Roast AI",
            value=(
                "`/roast`\n"
                "`/data`\n"
                "`/autor`\n"
                "`/roastmode`\n"
                "`/stoproast`"
            ),
            inline=False
        )
        embed.add_field(
            name="Codepad and Hacking",
            value=(
                "`/code_new`\n"
                "`/code_edit`\n"
                "`/code_view`\n"
                "`/code_list`\n"
                "`/code_delete`\n"
                "`/code_run`\n"
                "`/hack`\n"
                "`/hack_chaos`\n"
                "`/hack_profile`\n"
                "`/hack_targets`\n"
                "`/hack_chaos_state`"
            ),
            inline=False
        )
        embed.add_field(
            name="Other AI and Live Stuff",
            value=(
                "`/img`\n"
                "`/lichess`\n"
                "`/lichess_game`\n"
                "`/lichess_stream`"
            ),
            inline=False
        )
        embed.set_footer(text="good starter route: /roast or /code_list")
        return embed

    if topic == "admin":
        embed = discord.Embed(
            title="🛠️ help • admin",
            description="server onboarding and moderation tools",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Server Setup",
            value=(
                "`/setup view`\n"
                "`/setup channel`\n"
                "`/setup tips`\n"
                "`/setup post`\n"
                "`/setup reset`"
            ),
            inline=False
        )
        embed.add_field(
            name="AutoMod",
            value=(
                "`/automod`\n"
                "`/automod_reset`\n"
                "`/automod_punishment`\n"
                "`/automod_slurs`\n"
                "`/automod_spam`\n"
                "`/automod_filters`\n"
                "`/automod_settings`"
            ),
            inline=False
        )
        embed.add_field(
            name="Recommended Order",
            value=(
                "1. run `/setup channel`\n"
                "2. run `/setup post`\n"
                "3. run `/help start` yourself and check the flow\n"
                "4. turn on automod only if you want it"
            ),
            inline=False
        )
        embed.set_footer(text="admins should start with /setup view")
        return embed

    if topic == "fun":
        embed = discord.Embed(
            title="🎉 help • fun and extras",
            description="side commands, casual stuff, and social commands",
            color=discord.Color.fuchsia(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Casual Commands",
            value=(
                "`/afk`\n"
                "`/animal`\n"
                "`/badge`\n"
                "`/emojimixup`\n"
                "`/aki`\n"
                "`/img`"
            ),
            inline=False
        )
        embed.add_field(
            name="Interactive Games",
            value=(
                "`/battleship`\n"
                "`/battleship_resume`\n"
                "`/battleship_forfeit`\n"
                "`/battleship_stats`\n"
                "`/battleship_leaderboard`\n"
                "`/monopoly_start`\n"
                "`/monopoly_resume`\n"
                "`/monopoly_stop`"
            ),
            inline=False
        )
        embed.add_field(
            name="Extra Builders",
            value=(
                "`/rave`\n"
                "`/ravebg`"
            ),
            inline=False
        )
        embed.set_footer(text="these are the side dishes, not the main grind")
        return embed

    if topic == "all":
        embed = discord.Embed(
            title="📚 help • topic map",
            description="use `/help <topic>` with one of these categories",
            color=discord.Color.dark_gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(
            name="Topics",
            value=(
                "`start`\n"
                "`economy`\n"
                "`adventure`\n"
                "`deep`\n"
                "`ai`\n"
                "`admin`\n"
                "`fun`\n"
                "`all`"
            ),
            inline=False
        )
        embed.add_field(
            name="Fast Examples",
            value=(
                "`/help start`\n"
                "`/help economy`\n"
                "`/help adventure`\n"
                "`/help deep`\n"
                "`/help ai`\n"
                "`/help admin`\n"
                "`/help fun`"
            ),
            inline=False
        )
        embed.add_field(
            name="Best New User Route",
            value=(
                "`/profile`\n"
                "`/daily`\n"
                "`/work`\n"
                "`/help economy`\n"
                "`/help adventure`"
            ),
            inline=False
        )
        embed.set_footer(text="start with /help start if youre new")
        return embed

    embed = discord.Embed(
        title="👋 help • getting started",
        description=f"hey {user.mention} — this bot does a lot, so here’s the clean way to start without staring at the slash menu",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    embed.add_field(
        name="First Commands to Try",
        value=(
            "`/profile` see your account\n"
            "`/balance` check your money\n"
            "`/daily` claim free horsenncy\n"
            "`/work` earn more\n"
            "`/help economy` or `/help adventure`"
        ),
        inline=False
    )
    embed.add_field(
        name="Popular Routes",
        value=(
            "**money route**\n"
            "`/daily` → `/work` → `/shop` or `/stocks`\n\n"
            "**creature route**\n"
            "`/hunt` or `/fish` → `/team list` → `/battle`\n\n"
            "**deep route**\n"
            "`/dungeon` or `/voidmaze` or `/arena`\n\n"
            "**ai route**\n"
            "`/roast` or `/code_list` → `/hack`"
        ),
        inline=False
    )
    embed.add_field(
        name="Help Topics",
        value=(
            "`/help economy`\n"
            "`/help adventure`\n"
            "`/help deep`\n"
            "`/help ai`\n"
            "`/help admin`\n"
            "`/help fun`"
        ),
        inline=False
    )
    embed.set_footer(text="use the menu below to switch categories")
    return embed


class HelpTopicSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Start", value="start", emoji="👋", description="best first steps"),
            discord.SelectOption(label="Economy", value="economy", emoji="💰", description="money, items, stocks"),
            discord.SelectOption(label="Adventure", value="adventure", emoji="⚔️", description="hunt, fish, battle, dungeon"),
            discord.SelectOption(label="Deep Systems", value="deep", emoji="🌀", description="profile, quests, guilds"),
            discord.SelectOption(label="AI and Utility", value="ai", emoji="🤖", description="roast, code, hack, lichess"),
            discord.SelectOption(label="Admin", value="admin", emoji="🛠️", description="setup and automod"),
            discord.SelectOption(label="Fun", value="fun", emoji="🎉", description="extras and side commands"),
            discord.SelectOption(label="All Topics", value="all", emoji="📚", description="topic map"),
        ]
        super().__init__(placeholder="pick a help category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, HelpView):
            await interaction.response.send_message("help menu error", ephemeral=True)
            return
        if interaction.user.id != view.author_id:
            await interaction.response.send_message("not your help menu", ephemeral=True)
            return
        embed = make_embed(self.values[0], interaction.user)
        await interaction.response.edit_message(embed=embed, view=view)


class HelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.add_item(HelpTopicSelect())

STARTER_ROUTES = {
    "money": {
        "title": "💰 money route",
        "desc": "fast start for economy and progression",
        "steps": [
            "/profile",
            "/daily",
            "/work",
            "/shop",
            "/help economy",
        ],
    },
    "battle": {
        "title": "⚔️ battle route",
        "desc": "build a team and start fighting things",
        "steps": [
            "/profile",
            "/hunt",
            "/team list",
            "/battle",
            "/help adventure",
        ],
    },
    "ai": {
        "title": "🤖 ai route",
        "desc": "jump into the bot's ai side first",
        "steps": [
            "/roast",
            "/roastmode",
            "/code_list",
            "/hack",
            "/help ai",
        ],
    },
}

def make_start_embed(route_key: str, user: discord.abc.User) -> discord.Embed:
    if route_key == "home":
        embed = discord.Embed(
            title="🚀 start here",
            description=f"hey {user.mention} — pick the path you want and i’ll give you the fastest route",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(
            name="available paths",
            value=(
                "💰 money\n"
                "⚔️ battle\n"
                "🤖 ai"
            ),
            inline=False,
        )
        embed.set_footer(text="pick one below")
        return embed

    data = STARTER_ROUTES[route_key]
    embed = discord.Embed(
        title=data["title"],
        description=data["desc"],
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    embed.add_field(
        name="do these in order",
        value="\n".join(f"{i+1}. `{step}`" for i, step in enumerate(data["steps"])),
        inline=False,
    )
    embed.set_footer(text="finish this path first, then branch out")
    return embed

class StartView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=180)
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("not your menu", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="money", style=discord.ButtonStyle.success, emoji="💰")
    async def money_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=make_start_embed("money", interaction.user),
            view=self
        )

    @discord.ui.button(label="battle", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def battle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=make_start_embed("battle", interaction.user),
            view=self
        )

    @discord.ui.button(label="ai", style=discord.ButtonStyle.primary, emoji="🤖")
    async def ai_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=make_start_embed("ai", interaction.user),
            view=self
        )

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start", description="Get a guided starting route through FuSBot.")
    async def start(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_start_embed("home", interaction.user),
            view=StartView(interaction.user.id)
        )

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Learn how to use FuSBot.")
    @app_commands.describe(topic="start, economy, adventure, deep, ai, admin, fun, or all")
    async def help(self, interaction: discord.Interaction, topic: str = None):
        embed = make_embed(topic, interaction.user)
        view = HelpView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    print("Loading Help Cog...")
    await bot.add_cog(Help(bot))
    print("Help Cog Loaded!")
