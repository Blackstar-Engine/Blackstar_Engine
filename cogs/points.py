import discord
from discord.ext import commands
from utils.constants import profiles, departments
from ui.points.views.AcceptDenyButtons import AcceptDenyButtons
from ui.points.views.UnitSelect import UnitSelectView
from utils.utils import fetch_profile, fetch_unit_options, fetch_department


class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="points")
    async def points(self, ctx: commands.Context):
        return

    @points.command(name="request", description="Request points to be added to your profile")
    async def request(self, ctx: commands.Context, points: float, proof):
        if points <= 0 or not isinstance(points, float):
            return await ctx.send("Please make sure the number is positive and is an number.", ephemeral=True)
        
        # Fetch the profile
        profile = await fetch_profile(ctx)
        if not profile:
            return

        # Fetch the select options
        options = fetch_unit_options(profile)

        # Create the View and Embed
        unit_select_view = UnitSelectView(self.bot, options, profile)

        unit_select_embed = discord.Embed(title="Select a Unit", description="Please select a unit you would like this point request to send to!", color=discord.Color.light_grey())

        # Send and wait
        await ctx.send(embed=unit_select_embed, view=unit_select_view, ephemeral=True)

        await unit_select_view.wait()

        # Get returned values and check
        dept = unit_select_view.dept

        if dept == "no_unit":
            return await ctx.send("You do not have any active units to send this request to.", ephemeral=True)

        # Fetch the department and get the request channel
        department_doc = await fetch_department(ctx, dept)

        channel = ctx.guild.get_channel(int(department_doc.get("points_request_channel")))

        # Create the points request mod embed
        mod_embed = discord.Embed(title="New Points Request",
                                  description=f"**User: ** {ctx.author.mention}\n** Requested Points: ** {points}\n**Proof: ** {proof}",
                                  color=discord.Color.light_grey())
        
        current_points = profile['unit'][dept].get('current_points', 0)
        total_points = profile['unit'][dept].get('total_points', 0)

        mod_embed.add_field(name="__Profile Info:__",
                            value=f"> **Codename: ** {profile.get('codename')}\n> **Join Date: ** {profile.get('join_date')}\n> **{dept} Current Points: ** {current_points}\n> **{dept} Total Points: ** {total_points}")

        # Init the view and send the embed
        accept_deny_buttons_view = AcceptDenyButtons(self.bot, ctx.author, points, mod_embed, profile, dept)

        await channel.send(embed=mod_embed, view=accept_deny_buttons_view)

        # Create the users embed and send to the channel
        embed=discord.Embed(title="", 
                            description=f"**{points}** point(s) have been **successfully** requested!",
                            color=discord.Color.light_grey())

        await ctx.send(embed=embed, delete_after=10, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))