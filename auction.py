import datetime
import discord
from discord.ext import commands
from discord import app_commands

from economy import get_user
from economy_shared import state, save_state


def auction_root():
    return state.setdefault("auction_house_v1", {"next_id": 1, "listings": []})


def clean_listings():
    root = auction_root()
    now = datetime.datetime.utcnow()
    kept = []
    for listing in root.get("listings", []):
        expires_at = listing.get("expires_at")
        dt = None
        try:
            dt = datetime.datetime.fromisoformat(expires_at) if expires_at else None
        except Exception:
            dt = None
        if dt and dt <= now:
            seller = get_user(int(listing["seller_id"]))
            inventory = seller.setdefault("inventory", {})
            inventory[listing["item_name"]] = int(inventory.get(listing["item_name"], 0) or 0) + int(listing["amount"])
        else:
            kept.append(listing)
    root["listings"] = kept
    save_state()


def find_listing(listing_id: int):
    for listing in auction_root().get("listings", []):
        if int(listing.get("id", 0)) == int(listing_id):
            return listing
    return None


class Auction(commands.Cog):
    auction_group = app_commands.Group(name="auction", description="Auction house commands")

    def __init__(self, bot):
        self.bot = bot

    @auction_group.command(name="sell", description="List an inventory item on the auction house.")
    async def sell(self, interaction: discord.Interaction, item_name: str, amount: app_commands.Range[int, 1], price_each: app_commands.Range[int, 1]):
        clean_listings()
        data = get_user(interaction.user.id)
        inventory = data.setdefault("inventory", {})
        have = int(inventory.get(item_name, 0) or 0)
        if amount > have:
            await interaction.response.send_message("you dont have that many of that item", ephemeral=True)
            return
        inventory[item_name] = have - int(amount)
        if inventory[item_name] <= 0:
            inventory.pop(item_name, None)
        root = auction_root()
        listing = {
            "id": root["next_id"],
            "seller_id": interaction.user.id,
            "item_name": item_name,
            "amount": int(amount),
            "price_each": int(price_each),
            "created_at": datetime.datetime.utcnow().isoformat(),
            "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=2)).isoformat(),
        }
        root["next_id"] += 1
        root["listings"].append(listing)
        save_state()
        await interaction.response.send_message(f"listed `{amount}x {item_name}` for `{price_each}` each as listing `{listing['id']}`")

    @auction_group.command(name="browse", description="Browse the current auction house.")
    async def browse(self, interaction: discord.Interaction):
        clean_listings()
        listings = auction_root().get("listings", [])[:20]
        embed = discord.Embed(
            title="🛒 Auction House",
            description=f"active listings: `{len(auction_root().get('listings', []))}`",
            color=discord.Color.dark_gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if not listings:
            embed.add_field(name="Listings", value="nothing is up right now", inline=False)
        else:
            lines = []
            for listing in listings:
                total = int(listing["amount"]) * int(listing["price_each"])
                lines.append(
                    f"`{listing['id']}` **{listing['item_name']}** x{listing['amount']} • `{listing['price_each']}` each • total `{total}`"
                )
            embed.add_field(name="Listings", value="\n".join(lines), inline=False)
        embed.set_footer(text="use /auction buy <id> to buy or /auction cancel <id> to cancel your own listing")
        await interaction.response.send_message(embed=embed)

    @auction_group.command(name="buy", description="Buy an auction listing.")
    async def buy(self, interaction: discord.Interaction, listing_id: int):
        clean_listings()
        listing = find_listing(listing_id)
        if not listing:
            await interaction.response.send_message("that listing doesnt exist", ephemeral=True)
            return
        if int(listing["seller_id"]) == interaction.user.id:
            await interaction.response.send_message("you cant buy your own listing", ephemeral=True)
            return
        total = int(listing["amount"]) * int(listing["price_each"])
        buyer = get_user(interaction.user.id)
        seller = get_user(int(listing["seller_id"]))
        if int(buyer.get("balance", 0) or 0) < total:
            await interaction.response.send_message("not enough horsenncy", ephemeral=True)
            return
        buyer["balance"] = int(buyer.get("balance", 0) or 0) - total
        seller["balance"] = int(seller.get("balance", 0) or 0) + total
        inventory = buyer.setdefault("inventory", {})
        inventory[listing["item_name"]] = int(inventory.get(listing["item_name"], 0) or 0) + int(listing["amount"])
        auction_root()["listings"] = [x for x in auction_root().get("listings", []) if int(x.get("id", 0)) != int(listing_id)]
        save_state()
        await interaction.response.send_message(
            f"bought `{listing['amount']}x {listing['item_name']}` for `{total}` horsenncy from `<@{listing['seller_id']}>`"
        )

    @auction_group.command(name="cancel", description="Cancel your own auction listing.")
    async def cancel(self, interaction: discord.Interaction, listing_id: int):
        clean_listings()
        listing = find_listing(listing_id)
        if not listing:
            await interaction.response.send_message("that listing doesnt exist", ephemeral=True)
            return
        if int(listing["seller_id"]) != interaction.user.id:
            await interaction.response.send_message("thats not your listing", ephemeral=True)
            return
        data = get_user(interaction.user.id)
        inventory = data.setdefault("inventory", {})
        inventory[listing["item_name"]] = int(inventory.get(listing["item_name"], 0) or 0) + int(listing["amount"])
        auction_root()["listings"] = [x for x in auction_root().get("listings", []) if int(x.get("id", 0)) != int(listing_id)]
        save_state()
        await interaction.response.send_message(f"listing `{listing_id}` canceled and items returned")


async def setup(bot):
    print("Loading Auction Cog...")
    await bot.add_cog(Auction(bot))
    print("Auction Cog Loaded!")
