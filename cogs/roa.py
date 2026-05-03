import discord
from discord import ui
from discord.ext import commands
import re
from utils.constants import roa, stored_roa, loa, LOARegFormat
from datetime import datetime, timedelta
from ui.paginator import PaginatorView
from ui.roa.views.RequestButtons import RequestButtons
from ui.roa.views.ManageButtons import ManageExtendButton
from typing import Optional
from utils.utils import fetch_id, has_approval_perms, fetch_profile


class ROA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_accepted(self, ctx: commands.Context, view: RequestButtons, reason: str, start_date: datetime, end_date: datetime, time: str, request_message: discord.Message):
        moderator: discord.Member = view.action_row.kwargs.get('moderator_obj')
        loa_doc = {
                "user_id": ctx.author.id,
                "nickname": ctx.author.display_name,
                "guild_id": ctx.guild.id,
                "start_date": start_date,
                "end_date": end_date,
                "days": time,
                "reason": reason,
                "moderator_id": moderator.id
            }
        
        await roa.insert_one(loa_doc)

        results = await fetch_id(ctx.guild.id, ["loa_role"])
        loa_role = results["loa_role"]

        role = ctx.guild.get_role(loa_role)
        await ctx.author.add_roles(role)

        profile = await fetch_profile(ctx)
        if not profile:
            return
        codename = profile.get("codename", "N/A")

        units = profile["unit"]
        max_points = -1
        max_rank = None
        for _, value in units.items():
            if value["total_points"] > max_points:
                max_points = value["total_points"]
                max_rank = value["rank"]

        try:
            await ctx.author.edit(nick=f"[ROA|{max_rank}] {codename}")
        except discord.Forbidden:
            pass

        container = ui.Container(
            ui.TextDisplay("## Reduce of Activity Accepted"),
            ui.TextDisplay(f"**Member:** {ctx.author.mention}\n**Start:** {discord.utils.format_dt(start_date)}\n**End:** {discord.utils.format_dt(end_date)}\n**Reason:** ``{reason}``\n**Time:** ``{time}``"),
            ui.Separator(),
            ui.TextDisplay(f"**Accepted By: ** {moderator.mention}\n**Reason: ** {view.action_row.kwargs.get('reason', 'No reason provided.')}"),
            accent_color=discord.Color.green()

        )
        accepted_view = ui.LayoutView()
        accepted_view.add_item(container)

        try:
            await request_message.edit(view=accepted_view)
        except discord.NotFound:
            pass

        try:
            embed = discord.Embed(title="ROA Request Update", description=f"Your ROA request in **{ctx.guild.name}** has been **ACCEPTED**", color=discord.Color.green())
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            pass
    
    async def handle_denied(self, ctx: commands.Context, view: RequestButtons, start_date: datetime, end_date: datetime, reason: str, time: str, request_message: discord.Message):
        moderator: discord.Member = view.action_row.kwargs.get('moderator_obj')
        container = ui.Container(
                ui.TextDisplay("## Reduce of Activity Denied"),
                ui.TextDisplay(f"**Member:** {ctx.author.mention}\n**Start:** {discord.utils.format_dt(start_date)}\n**End:** {discord.utils.format_dt(end_date)}\n**Reason:** ``{reason}``\n**Time:** ``{time}``"),
                ui.Separator(),
                ui.TextDisplay(f"**Denied By: ** {moderator.mention}\n**Reason: ** {view.action_row.kwargs.get('reason', 'No reason provided.')}"),
                accent_color=discord.Color.red()

            )
        denied_view = ui.LayoutView()
        denied_view.add_item(container)

        try:
            await request_message.edit(view=denied_view)
        except discord.NotFound:
            pass

        try:
            embed = discord.Embed(title="ROA Request Update", description=f"Your ROA request in **{ctx.guild.name}** has been **DENIED**\n**Reason: ** {view.action_row.kwargs.get('reason', 'No reason provided.')} ", color=discord.Color.red())
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.hybrid_group(name="roa", description="Create a roa", invoke_without_sub_command=False)
    async def roa(self, ctx: commands.Context):
        return

    @roa.command(description="Request an ROA to get time off.")
    async def request(self, ctx: commands.Context, time: str, reason: str):
        def extract_time_values(time_string):
            # Create a reg match
            search = re.match(LOARegFormat,time_string)

            # Check to see if it returns none or improper groups
            if search is None or search.group() == "":
                return 0, 0, 0, 0, 0
            
            # Return full list of items
            return map(int, search.groups(default="0"))

        error_embed = discord.Embed(title="", description="")

        loa_record = await loa.find_one({"user_id": ctx.author.id, "guild_id": ctx.guild.id})
        if loa_record:
            error_embed.description = "You have an active LOA. Please end it before starting a ROA."
            return await ctx.send(embed=error_embed, ephemeral=True)
        
        # If time does not = the correct format, return
        if not re.match(LOARegFormat, time):
            error_embed.description = "Please use the correct time format: \n**<number>y<number>m<number>w<number>d<number>h**\n\n**__Examples:__**\n> `1y2m3w4d5h` = 1 year, 2 months, 3 weeks, 4 days, and 5 hours\n> `2w4d` = 2 weeks and 4 days\n> `5h` = 5 hours"
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Find a record for the user and return if record is found
        loa_record = await roa.find_one({"user_id": ctx.author.id, "guild_id": ctx.guild.id})

        if loa_record:
            error_embed.description = "You already have an active ROA. Please end it before starting a new one."
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Break time into y, m, w, d, h and find total days from that
        years, months, weeks, days, hours = extract_time_values(time)
        total_days = years * 365 + months * 30 + weeks * 7 + days

        # Find y, m, w, d, h from roa min and max
        min_years, min_months, min_weeks, min_days, _ = extract_time_values('1d')
        max_years, max_months, max_weeks, max_days, _ = extract_time_values('1y')

        # Find total days for roa min and max
        min_total_days = min_years * 365 + min_months * 30 + min_weeks * 7 + min_days
        max_total_days = max_years * 365 + max_months * 30 + max_weeks * 7 + max_days

        # Checks to see if the requested days is in between the min and max days
        if total_days < min_total_days:
            error_embed.description = "ROA time does not meet the minimum ROA time."
            return await ctx.send(embed=error_embed, ephemeral=True)
        elif total_days > max_total_days:
            error_embed.description = "ROA time exceeds the maximum ROA time."
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Creates the needed material for the request embed
        start_date = datetime.now()
        end_date = start_date + timedelta(days=total_days, hours=hours)
        
        # Creats the View and sends the message to the loa_channel
        results = await fetch_id(ctx.guild.id, ["loa_channel"])
        channel: discord.TextChannel = await ctx.guild.fetch_channel(results["loa_channel"])

        view = RequestButtons(self.bot, ctx.author, reason, start_date, end_date, time)
        request_message = await channel.send(view=view)

        # Sends confirmation to user
        embed = discord.Embed(title="Successfully Requested!", description="Your ROA has been sent in for review!", color=discord.Color.green())
        await ctx.send(embed=embed, delete_after=10)

        await view.wait()
        if not view.action_row.is_accepted:
            await self.handle_denied(ctx, view, start_date, end_date, reason, time, request_message)
        else:
            await self.handle_accepted(ctx, view, reason, start_date, end_date, time, request_message)

    @roa.command(description="Get a list of all the active ROA's in the server.")
    async def active(self, ctx: commands.Context):
        # Users have to be in foundation or site command to run this command
        if not await has_approval_perms(ctx, 5):
            return
        
        # Find all ROA's, create the view, create the embed, send to user
        items = await roa.find({'guild_id': ctx.guild.id}).to_list(length=None)
        view = PaginatorView(self.bot, ctx.author, items)
        embed = view.create_record_embed()

        await ctx.send(embed=embed, view=view, ephemeral=True)

    @roa.command(description="Manage a staff members ROA.")
    async def manage(self, ctx: commands.Context, user: Optional[discord.Member | discord.User] = None):
        # Checking if user selected themselves
        if not user or user.id == ctx.author.id:
            member = ctx.author
        else:
            # If they are managing another user, they need to be in foundation or site command
            if not await has_approval_perms(ctx, 5):
                return
            
            member = user

        # Finding all active and stored roas for that user in that guild
        active_roa = await roa.find_one({"user_id": member.id, "guild_id": ctx.guild.id})
        stored_roas = await stored_roa.find({"user_id": member.id, "guild_id": ctx.guild.id}).to_list(length=None)
        
        if not active_roa and stored_roas == []:
            embed = discord.Embed(title="", description=f"{member.mention} has no ROA's to manage")
            return await ctx.send(embed=embed, ephemeral=True)

        # Creating the "history" part of the embed
        des = ""

        des = "\n".join(
            [
                f"{discord.utils.format_dt(roa['start_date'])} - {discord.utils.format_dt(roa['end_date'])}"
                for roa in stored_roas
            ]
        )

        # Create the rest of the embed
        view = ManageExtendButton(self.bot, ctx.author, member, active_roa, des)

        await ctx.send(view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ROA(bot))