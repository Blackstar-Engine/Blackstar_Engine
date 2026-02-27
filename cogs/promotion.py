import discord
from discord.ext import commands
from ui.promotion.views.PromotionRequest import PromotionRequestView
from utils.utils import fetch_profile, fetch_department, generate_timestamp
import uuid
from utils.constants import promotion_requests

async def send_promotion_request(bot, channel, profile, dept_name, proof, new_rank):
    
    request_id = str(uuid.uuid4())

    snapshot = {
        "user_id": profile["user_id"],
        "codename": profile.get("codename"),
        "status": profile.get("status"),
        "department": dept_name,
        "current_rank": profile["unit"][dept_name]["rank"],
        "new_rank": new_rank,
        "proof": proof,
        "current_points": profile["unit"][dept_name]["current_points"],
        "total_points": profile["unit"][dept_name]["total_points"],
        "join_timestamp": generate_timestamp(profile["join_date"])
    }

    view = PromotionRequestView(bot, request_id, snapshot)
    msg = await channel.send(view=view)

    await promotion_requests.insert_one({
        "_id": request_id,
        "guild_id": channel.guild.id,
        "target_user_id": profile["user_id"],
        "snapshot": snapshot,
        "message_id": msg.id,
        "channel_id": channel.id,
        "is_active": True
    })

class Promotion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="promotion", invoke_without_command=True)
    async def promotion(self, ctx: commands.Context):
        await ctx.send("Available subcommands: request")

    @promotion.command(name="request", description="Request a promotion in a department.")
    async def request(self, ctx: commands.Context, department: str, *, proof: str):
        await ctx.defer(ephemeral=True)

        # Fetch the profile
        profile = await fetch_profile(ctx)
        if not profile:
            return

        # fetch the department
        department_doc = await fetch_department(ctx, department)
        if not department_doc:
            return

        dept_name = department_doc["display_name"]

        # Check to see if they are an active member
        unit_data = profile.get("unit", {}).get(dept_name)

        if not unit_data or not unit_data.get("is_active"):
            embed = discord.Embed(title="", description="You are not an active member of this department.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        current_rank_name = unit_data.get("rank")

        # Get the current rank
        ranks = sorted(department_doc.get("ranks", []), key=lambda r: r["order"])

        current_rank = next(
            (r for r in ranks if r["name"] == current_rank_name),
            None
        )

        if not current_rank:
            embed = discord.Embed(title="", description="Your current rank could not be resolved.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        # Get the next rank
        next_rank = next(
            (r for r in ranks if r["order"] == current_rank["order"] + 1),
            None
        )

        if not next_rank:
            embed = discord.Embed(title="", description="You are already at the highest rank.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        if next_rank.get("appointment_only"):
            embed = discord.Embed(title="", description=f"{next_rank['name']} is an appointment-only rank.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        # Send the request to the mods
        channel = ctx.guild.get_channel(department_doc.get("promo_request_channel"))
        if not channel:
            embed = discord.Embed(title="Error!", description="Promotion request channel not found. Please contact DSM!", color=discord.Color.red())
            return await ctx.send(embed=embed, ephemeral=True)

        await send_promotion_request(self.bot, channel, profile, dept_name, proof, next_rank['name'])

        await ctx.send("Promotion request submitted.", ephemeral=True, delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(Promotion(bot))