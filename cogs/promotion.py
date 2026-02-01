import discord
from discord.ext import commands
from utils.constants import departments
from ui.promotion.views.PromotionRequest import PromotionRequestView
from utils.utils import fetch_profile, fetch_department


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

        embed = discord.Embed(
            title="Promotion Request",
            color=discord.Color.light_grey()
        )
        embed.add_field(name="Member", value=ctx.author.mention, inline=False)
        embed.add_field(name="Department", value=dept_name, inline=True)
        embed.add_field(name="Current Rank", value=current_rank_name, inline=True)
        embed.add_field(name="Requested Rank", value=next_rank["name"], inline=True)
        embed.add_field(name="Proof", value=proof, inline=False)

        view = PromotionRequestView(
            self.bot,
            ctx.author,
            embed,
            profile,
            dept_name,
            next_rank["name"],
        )
        await channel.send(embed=embed, view=view)

        await ctx.send("Promotion request submitted.", ephemeral=True, delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(Promotion(bot))