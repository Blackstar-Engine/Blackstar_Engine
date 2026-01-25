import discord
from discord.ext import commands

from utils.constants import (
    foundation_command,
    site_command,
    high_command,
    central_command,
    wolf_id,
    profiles,
    departments
)

def has_approval_perms(member: discord.Member) -> bool:
    allowed_roles = {
        foundation_command,
        site_command,
        high_command,
        central_command,
    }

    if member.id == wolf_id:
        return True

    return any(role.id in allowed_roles for role in member.roles)

class PromotionRequestView(discord.ui.View):
    def __init__(self, user: discord.Member, embed: discord.Embed, profile, department, new_rank, points):
        super().__init__(timeout=None)
        self.user = user
        self.embed = embed
        self.profile = profile
        self.department = department
        self.new_rank = new_rank
        self.points = points

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not has_approval_perms(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to approve promotions.",
                ephemeral=True
            )
            return
        
        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {
                "$set": {
                    f"unit.{self.department}.rank": self.new_rank
                },
                "$inc": {
                    "current_points": -abs(self.points)
                }
            }
        )

        self.embed.title = "Promotion Approved"
        self.embed.color = discord.Color.green()

        await interaction.message.edit(embed=self.embed, view=None)

        await self.user.send(f"Your Promotion to **{self.new_rank}** in **{interaction.guild.name}** has been **APPROVED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not has_approval_perms(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to deny promotions.",
                ephemeral=True
            )
            return

        self.embed.title = "Promotion Denied"
        self.embed.color = discord.Color.red()

        await interaction.message.edit(embed=self.embed, view=None)

        await self.user.send(f"Your Promotion to **{self.new_rank}** in **{interaction.guild.name}** has been **DENIED**")


class Promotion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="promotion", invoke_without_command=True)
    async def promotion(self, ctx: commands.Context):
        await ctx.send("Available subcommands: request")

    @promotion.command(name="request", description="Request a promotion in a department.")
    async def request(self, ctx: commands.Context, *, department: str):
        await ctx.defer(ephemeral=True)

        profile = await profiles.find_one(
            {"user_id": ctx.author.id, "guild_id": ctx.guild.id}
        )

        if not profile:
            embed = discord.Embed(title="", description="Profile Not Found", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        # ─── Find department ───
        dept = await departments.find_one({
            "$or": [
                {"name": department},
                {"display_name": department}
            ]
        })

        if not dept:
            embed = discord.Embed(title="", description="Department not found.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        dept_name = dept["display_name"]

        # ─── Membership + active check ───
        unit_data = profile.get("unit", {}).get(dept_name)

        if not unit_data or not unit_data.get("is_active"):
            embed = discord.Embed(title="", description="You are not an active member of this department.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        current_rank_name = unit_data.get("rank")

        # ─── Resolve ranks ───
        ranks = sorted(dept.get("ranks", []), key=lambda r: r["order"])

        current_rank = next(
            (r for r in ranks if r["name"] == current_rank_name),
            None
        )

        if not current_rank:
            embed = discord.Embed(title="", description="Your current rank could not be resolved.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        next_rank = next(
            (r for r in ranks if r["order"] == current_rank["order"] + 1),
            None
        )

        if not next_rank:
            embed = discord.Embed(title="", description="You are already at the highest rank.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        if next_rank.get("appointment_only"):
            embed = discord.Embed(title="", description="This rank is appointment-only.", color=discord.Color.dark_embed())
            return await ctx.send(embed=embed, ephemeral=True)

        # ─── Points check ───
        cur = profile.get("current_points", 0)
        total = profile.get("total_points", 0)
        req = next_rank.get("required_points", {})

        if cur < req.get("current", 0) or total < req.get("total", 0):
            embed = discord.Embed(title="Permission Denied", description=f"Points Required for {next_rank.get("name")}\n\n> **Current Points:** {req.get('current', 0)}\n> **Total Points: ** {req.get('total', 0)}", color=discord.Color.red())
            return await ctx.send(embed=embed, ephemeral=True)

        # ─── Send request ───
        channel = ctx.guild.get_channel(dept.get("promo_request_channel"))
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
        embed.add_field(
            name="Points",
            value=f"{cur} current / {total} total",
            inline=False
        )

        required_current = req.get("current", 0)

        view = PromotionRequestView(
            ctx.author,
            embed,
            profile,
            dept_name,
            next_rank["name"],
            required_current
        )
        await channel.send(embed=embed, view=view)

        await ctx.send("Promotion request submitted.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Promotion(bot))