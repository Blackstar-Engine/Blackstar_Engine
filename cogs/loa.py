import discord
from discord.ext import commands
import re
from utils.constants import loa, stored_loa, LOARegFormat, loa_channel, foundation_command, site_command
from datetime import datetime, timedelta
from ui.paginator import PaginatorView
from ui.loa.views.RequestAcceptDenyButtons import RequestAcceptDenyButtons
from ui.loa.views.ManageExtendButtons import ManageExtendButton
from typing import Optional


class LOA(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="loa", description="Create a loa", invoke_without_sub_command=False)
    async def loa(self, ctx: commands.Context):
        return

    @loa.command(description="Request an LOA to get time off.")
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
        
        # If time does not = the correct format, return
        if not re.match(LOARegFormat, time):
            error_embed.description = "Please use the correct time format: \n**<number>y<number>m<number>w<number>d<number>h**\n\n**__Examples:__**\n> `1y2m3w4d5h` = 1 year, 2 months, 3 weeks, 4 days, and 5 hours\n> `2w4d` = 2 weeks and 4 days\n> `5h` = 5 hours"
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Find a record for the user and return if record is found
        loa_record = await loa.find_one({"user_id": ctx.author.id, "guild_id": ctx.guild.id})

        if loa_record:
            error_embed.description = "You already have an active LOA. Please end it before starting a new one."
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Break time into y, m, w, d, h and find total days from that
        years, months, weeks, days, hours = extract_time_values(time)
        total_days = years * 365 + months * 30 + weeks * 7 + days

        # Find y, m, w, d, h from loa min and max
        min_years, min_months, min_weeks, min_days, _ = extract_time_values('1d')
        max_years, max_months, max_weeks, max_days, _ = extract_time_values('1y')

        # Find total days for loa min and max
        min_total_days = min_years * 365 + min_months * 30 + min_weeks * 7 + min_days
        max_total_days = max_years * 365 + max_months * 30 + max_weeks * 7 + max_days

        # Checks to see if the requested days is in between the min and max days
        if total_days < min_total_days:
            error_embed.description = "LOA time does not meet the minimum LOA time."
            return await ctx.send(embed=error_embed, ephemeral=True)
        elif total_days > max_total_days:
            error_embed.description = "LOA time exceeds the maximum LOA time."
            return await ctx.send(embed=error_embed, ephemeral=True)

        # Creates the needed material for the request embed
        start_date = datetime.now()
        end_date = start_date + timedelta(days=total_days, hours=hours)

        
        request_embed = discord.Embed(
            title="Leave Of Absence Request",
            description="",
            colour=discord.Color.yellow(),
        )
        request_embed.add_field(
            name="Information",
            value=f"**Member:** {ctx.author.mention}\n**Start:** {discord.utils.format_dt(start_date)}\n**End:** {discord.utils.format_dt(end_date)}\n**Reason:** ``{reason}``\n**Time:** ``{time}``",
        )

        if not ctx.author.avatar.url:
            request_embed.set_author(
                icon_url=ctx.author.default_avatar.url, name=f"{ctx.author.name}"
            )
        else:
            request_embed.set_author(
                icon_url=ctx.author.avatar.url, name=f"{ctx.author.name}"
            )
        
        # Creats the View and sends the message to the loa_channel
        channel: discord.TextChannel = await self.bot.fetch_channel(loa_channel)

        view = RequestAcceptDenyButtons(self.bot, ctx.author, reason, start_date, end_date, time, request_embed)
        await channel.send(embed=request_embed, view=view)

        # Sends confirmation to user
        embed = discord.Embed(title="Successfully Requested!", description="Your LOA has been sent in for review!", color=discord.Color.green())
        await ctx.send(embed=embed, delete_after=10)

    @loa.command(description="Get a list of all the active LOA's in the server.")
    async def active(self, ctx: commands.Context):
        # Users have to be in foundation or site command to run this command
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        # Find all LOA's, create the view, create the embed, send to user
        items = await loa.find({'guild_id': ctx.guild.id}).to_list(length=None)
        view = PaginatorView(self.bot, ctx.author, items)
        embed = view.create_record_embed()

        await ctx.send(embed=embed, view=view, ephemeral=True)

    @loa.command(description="Manage a staff members LOA.")
    async def manage(self, ctx: commands.Context, user: Optional[discord.Member | discord.User] = None):
        # Checking if user selected themselves
        if not user or user.id == ctx.author.id:
            member = ctx.author
        else:
            # If they are managing another user, they need to be in foundation or site command
            foundation_role = await ctx.guild.fetch_role(foundation_command)
            site_role = await ctx.guild.fetch_role(site_command)

            if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
                return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
            
            member = user

        # Finding all active and stored loas for that user in that guild
        active_loa = await loa.find_one({"user_id": member.id, "guild_id": ctx.guild.id})
        stored_loas = await stored_loa.find({"user_id": member.id, "guild_id": ctx.guild.id}).to_list(length=None)
        
        if not active_loa and stored_loas == []:
            embed = discord.Embed(title="", description=f"{member.mention} has no LOA's to manage")
            return await ctx.send(embed=embed, ephemeral=True)

        # Creating the "history" part of the embed
        des = ""

        des = "\n".join(
            [
                f"{discord.utils.format_dt(loa['start_date'])} - {discord.utils.format_dt(loa['end_date'])}"
                for loa in stored_loas
            ]
        )

        # Create the rest of the embed
        embed = discord.Embed(title="Leave Of Absence Admin Panel", description=f"LOA History {member.mention}:\n{des}")

        if not member.avatar.url:
            embed.set_author(icon_url=member.default_avatar.url, name=member.name)
        else:
            embed.set_author(icon_url=member.avatar.url, name=member.name)
        
        # If theres an active loa, send it. if not than just send the history
        if active_loa:
            embed.add_field(
                name="Current Leave Of Absence",
                value=f"**Started:** {discord.utils.format_dt(active_loa.get("start_date"))}\n**Ending:** {discord.utils.format_dt(active_loa.get("end_date"))}\n**Reason:** ``{active_loa.get("reason")}``\n**Moderator:** <@{active_loa.get("moderator_id")}>",
                inline=False
            )

            view = ManageExtendButton(self.bot, ctx.author, member, active_loa)
        else:
            view = None
        await ctx.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(LOA(bot))