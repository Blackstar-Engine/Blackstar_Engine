import discord
from discord.ext import commands
from ui.points.views.AcceptDenyButtons import PointsRequestView
from ui.points.views.UnitSelect import UnitSelectView
from utils.utils import fetch_profile, fetch_unit_options, fetch_department, generate_timestamp
import uuid
from utils.constants import point_requests

async def send_points_request(channel, profile, dept_name, points, proof):
    request_id = str(uuid.uuid4())

    snapshot = {
        "user_id": profile["user_id"],
        "codename": profile.get("codename"),
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

        # Send and wait
        select_message = await ctx.send(view=unit_select_view, ephemeral=True)

        await unit_select_view.wait()

        # Get returned values and check
        dept = unit_select_view.dept

        if dept == "no_unit":
            return await ctx.send("You do not have any active units to send this request to.", ephemeral=True)

        # Fetch the department and get the request channel
        department_doc = await fetch_department(ctx, dept)

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

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))