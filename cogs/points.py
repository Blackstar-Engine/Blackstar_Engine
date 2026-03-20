import discord
from discord.ext import commands
from ui.points.views.AcceptDenyButtons import PointsRequestView
from ui.points.views.UnitSelect import UnitSelectView
from utils.utils import fetch_profile, fetch_unit_options, fetch_department, generate_timestamp, fetch_id, has_approval_perms, log_action
import uuid
from utils.constants import point_requests, profiles
from datetime import datetime

async def send_points_request(channel, profile, dept_name, points, proof):
    request_id = str(uuid.uuid4())

    snapshot = {
        "user_id": profile["user_id"],
        "codename": profile["codename"],
        "department": dept_name,
        "points": float(points),
        "proof": proof,
        "current_points": profile["unit"][dept_name].get("current_points", 0),
        "total_points": profile["unit"][dept_name].get("total_points", 0),
        "join_timestamp": generate_timestamp(profile["join_date"])
    }

    view = PointsRequestView(request_id, snapshot)
    msg = await channel.send(view=view)

    await point_requests.insert_one({
        "_id": request_id,
        "guild_id": channel.guild.id,
        "target_user_id": profile["user_id"],
        "snapshot": snapshot,
        "message_id": msg.id,
        "channel_id": channel.id,
        "is_active": True
    })

class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_limit(self, ctx: commands.Context, results):
        limit = None
        if ctx.author.id == 1371489554279825439:
                limit = 999999999999999
        elif ctx.guild.get_role(results["foundation_command"]) in ctx.author.roles:
            limit = 5
        elif ctx.guild.get_role(results["site_command"]) in ctx.author.roles:
            limit = 3
        elif ctx.guild.get_role(results["high_command"]) in ctx.author.roles:
            limit = 2
        elif ctx.guild.get_role(results["central_command"]) in ctx.author.roles:
            limit = 1
        else:
            await ctx.send("Something went wrong, please contact **DSM**!", ephemeral=True)
            return False
        
        return limit

    @commands.hybrid_group(name="points")
    async def points(self, ctx: commands.Context):
        return

    @points.command(name="request", description="Request points to be added to your profile")
    async def request(self, ctx: commands.Context, points: float, *, proof: str):
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

        # Send and wait
        select_message = await ctx.send(view=unit_select_view, ephemeral=True)

        await unit_select_view.wait()

        # Get returned values and check
        dept = unit_select_view.dept

        if not dept or dept == "no_unit":
            return await ctx.send("You do not have any active units to send this request to.", ephemeral=True)

        # Fetch the department and get the request channel
        department_doc = await fetch_department(ctx, dept)
        if not department_doc:
            return

        channel = ctx.guild.get_channel(int(department_doc.get("points_request_channel")))

        await send_points_request(channel, profile, dept, points, proof)

        # Create the users embed and send to the channel
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"**{points}** point(s) have been **successfully** requested!"),
            accent_color=discord.Color.light_grey()
        )
        view.add_item(container)

        await select_message.edit(view=view)

    @points.command(name="gift", description="Gift points to other units")
    async def gift(self, ctx: commands.Context, user: discord.Member, points: int, *, reason: str):
        results = await fetch_id(
            ctx.guild.id,
            ["central_command", "foundation_command", "high_command", "site_command"]
        )

        # Check to make sure they can run this command
        if not await has_approval_perms(ctx.author, 3):
            return await ctx.send("This is only for Central Command+", ephemeral=True)

        # Command parsing checks
        if ctx.author.id == user.id:
            return await ctx.send("You can not gift points to yourself!", ephemeral=True)
        elif points <= 0:
            return await ctx.send("You must gift a positive number of points.", ephemeral=True)

        # Calculate the gifting point limit
        limit = await self._get_limit(ctx, results)
        if not limit:
            return

        authors_profile = await fetch_profile(ctx)
        if not authors_profile:
            return
        
        users_profile = await profiles.find_one({'guild_id': ctx.guild.id, 'user_id': user.id})
        if not users_profile:
            embed = discord.Embed(title="", description="Profile Not Found", color=discord.Color.dark_embed())
            await ctx.send(embed=embed)

        # Reinit gifting if new month
        gifted = authors_profile.setdefault("gifted", {})

        gifted.setdefault("gifted_points", 0)
        gifted.setdefault("current_month", 0)

        if gifted["current_month"] != datetime.now().month:
            gifted["gifted_points"] = 0
            gifted["current_month"] = datetime.now().month
        
        # Check if they have exceeded their limit for the month
        gifted_total = gifted["gifted_points"]
        if gifted_total + points > limit:
            return await ctx.send("You have exceeded your gifting limit!", ephemeral=True)              

        # Ask what department they want to use
        options = fetch_unit_options(users_profile)
        unit_select_view = UnitSelectView(self.bot, options, users_profile)
        await ctx.send(view=unit_select_view, ephemeral=True)
        await unit_select_view.wait()

        # After selection parsing
        dept = unit_select_view.dept

        if not dept or dept == "no_unit":
            return
        
        department_doc = await fetch_department(ctx, dept)
        if not department_doc:
            return

        channel = ctx.guild.get_channel(int(department_doc.get("points_request_channel")))

        new_total_points = gifted["gifted_points"] + points
        new_current_month = gifted["current_month"]

        await log_action(ctx=ctx, log_type="point_addition", user_id=user.id, points=points)

        # Update the authors profile
        await profiles.update_one(
            {"guild_id": ctx.guild.id, "user_id": ctx.author.id},
            {
                "$set": {
                    "gifted.current_month": new_current_month,
                    "gifted.gifted_points": new_total_points
                }
            },
            upsert=True
        )        

        # Update the recipient profile
        await profiles.update_one(
            {"guild_id": ctx.guild.id, "user_id": user.id},
            {"$inc": {
                        f"unit.{dept}.current_points": points,
                        f"unit.{dept}.total_points": points
                    }},
            upsert=True
        )  
        
        embed = discord.Embed(description=f"## Point Gift\n> **Point Gifter:** {ctx.author.mention}\n> **Points:** {points}\n> **Gifted To:** {user.mention}\n> **Reason:** {reason}", color=discord.Color.green())
        await channel.send(embed=embed)

        await ctx.send('Gift successfully sent!', ephemeral=True)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))