import discord
from discord.ext import commands
import datetime
import re
from utils.constants import loa, stored_loa, LOARegFormat, loa_min, loa_max, loa_channel, loa_role, foundation_command, site_command
import datetime
from datetime import datetime, timedelta
from utils.ui.paginator import PaginatorView

class EndLOAModal(discord.ui.Modal):
    def __init__(self, bot, user, member, active_loa):
        super().__init__(title="Provide a Reason")
        self.bot = bot
        self.user = user
        self.member = member
        self.active_loa = active_loa

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Because i said so!",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value

        channel = await interaction.guild.fetch_channel(loa_channel)

        await stored_loa.insert_one(self.active_loa)
        await loa.delete_one(self.active_loa)

        log_embed = discord.Embed(
            title="LOA Ended",
            description=f"**User: ** <@{self.active_loa.get("user_id")}>\n**Start Time: ** {discord.utils.format_dt(self.active_loa.get('start_date'))}\n**End Date: ** {discord.utils.format_dt(self.active_loa.get('end_date'))}\n**End Reason: ** {reason}",
            color=discord.Color.light_grey()
        )

        await channel.send(embed=log_embed)

        embed = discord.Embed(
            title="Leave of Absence Ended",
            description=f"You have successfully ended your LOA from {discord.utils.format_dt(self.active_loa.get('start_date'))} - {discord.utils.format_dt(self.active_loa.get('end_date'))}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ExtendAcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, active_loa, new_end_date, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.User = user
        self.active_loa = active_loa
        self.new_end_date = new_end_date
        self.embed: discord.Embed = embed

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.title = "Extention Approved"
        self.embed.color = discord.Color.green()
        self.embed.add_field(name="Approved by", value=interaction.user.mention)

        await interaction.response.edit_message(embed=self.embed, view=None)

        await loa.update_one(self.active_loa, {'$set': {'end_date': self.new_end_date}})

        role = await interaction.guild.fetch_role(loa_role)

        await self.user.add_roles(role)
        await self.user.send(f"Your LOA time extention in **{interaction.guild.name}** has been **ACCEPTED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequestDenyModal(self.bot)
        await interaction.response.send_modal(modal)

        await modal.wait()

        reason = modal.reason.value

        self.embed.title = "Extention Denied"
        self.embed.color = discord.Color.red()
        self.embed.add_field(name="Denied Information", value=f"**Denied By: ** {interaction.user.mention}\n**Reason: ** {reason}")

        await interaction.edit_original_response(embed=self.embed, view=None)

        await self.user.send(f"Your LOA time extention in **{interaction.guild.name}** has been **DENIED**\n**Reason: ** {reason}")

class AddTimeModal(discord.ui.Modal):
    def __init__(self, bot, active_loa, user, member):
        super().__init__(title="LOA Time Addition")
        self.bot = bot
        self.active_loa = active_loa
        self.user = user
        self.member = member

        self.time = discord.ui.TextInput(
            label="How Much Time",
            placeholder="e.g. 2w, 4h, or 5d",
            required=True,
            row=1,
            style=discord.TextStyle.short
        )
        self.add_item(self.time)

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="I need more time",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        time_input_value = self.time.value
        reason = self.reason.value

        match = re.match(LOARegFormat, time_input_value)

        if not match:
            await interaction.response.send_message("Invalid time format. Use '1y2m3w4d5h' for a combination of years, months, weeks, days, and hours.")
            return

        years, months, weeks, days, hours = map(int, match.groups(default="0"))

        time_delta = timedelta(days=years * 365 + months * 30 + weeks * 7 + days, hours=hours)

        new_end_date = self.active_loa["end_date"] + time_delta
        if self.member == self.user:  # If managing your own LOA
            channel = await interaction.guild.fetch_channel(loa_channel)

            request_embed = discord.Embed(
                title="LOA Extension Request",
                description=f"**Member:** {self.member.mention}\n**Requested by:** {interaction.user.mention}\n**New End Date:** {discord.utils.format_dt(new_end_date)}\n**Reason:** {reason}",
                colour=discord.Color.yellow()
            )

            view = ExtendAcceptDenyButtons(self.bot, self.user, self.active_loa, new_end_date, request_embed)

            await channel.send(embed=request_embed, view=view)

            extend_embed = discord.Embed(
                title="LOA Extention",
                description=f"Successfully sent the request. The LOA will end at {discord.utils.format_dt(new_end_date)}",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=extend_embed, ephemeral=True)

        else:  # If managing someone else's LOA
            await loa.update_one(self.active_loa, {'$set': {'end_date': new_end_date}})

            channel = await interaction.guild.fetch_channel(loa_channel)

            log_embed = discord.Embed(
                title="LOA Extended By Moderator",
                description=f"**User: ** <@{self.active_loa.get("user_id")}>\n**Start Time: ** {self.active_loa.get('start_date')}\n**End Date: ** {new_end_date}\n**End Reason: ** {reason}",
                color=discord.Color.light_grey()
            )

            await channel.send(embed=log_embed)

            extend_embed = discord.Embed(
                title="LOA Extention",
                description=f"Successfully extended {self.member.mention}'s LOA. The LOA will end at {discord.utils.format_dt(new_end_date)}",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=extend_embed, ephemeral=True)

class ManageExtendButton(discord.ui.View):
    def __init__(self, bot, user, member, document):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.member = member
        self.document = document

    @discord.ui.button(label="Extend", style=discord.ButtonStyle.green)
    async def manage_entend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddTimeModal(self.bot, self.document, self.user, self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="End", style=discord.ButtonStyle.red)
    async def manage_end_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        loa_end_modal = EndLOAModal(self.bot, self.user, self.member, self.document)
        await interaction.response.send_modal(loa_end_modal)

class RequestDenyModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Provide a Reason")
        self.bot = bot

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Because i said so!",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
class RequestAcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, reason, start_date, end_date, time, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.User = user
        self.time = time
        self.reason = reason
        self.start_date = start_date
        self.end_date = end_date
        self.embed: discord.Embed = embed

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.title = "Leave Of Absence Approved"
        self.embed.color = discord.Color.green()
        self.embed.add_field(name="Approved by", value=interaction.user.mention)

        await interaction.response.edit_message(embed=self.embed, view=None)

        loa_doc = {
            "user_id": self.user.id,
            "guild_id": interaction.guild.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days": self.time,
            "reason": self.reason,
            "moderator_id": interaction.user.id
        }
        await loa.insert_one(loa_doc)

        role = await interaction.guild.fetch_role(loa_role)

        await self.user.add_roles(role)
        await self.user.send(f"Your LOA in **{interaction.guild.name}** has been **ACCEPTED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequestDenyModal(self.bot)
        await interaction.response.send_modal(modal)

        await modal.wait()

        reason = modal.reason.value

        self.embed.title = "Leave Of Absence Denied"
        self.embed.color = discord.Color.red()
        self.embed.add_field(name="Denied Information", value=f"**Denied By: ** {interaction.user.mention}\n**Reason: ** {reason}")

        await interaction.edit_original_response(embed=self.embed, view=None)

        await self.user.send(f"Your LOA in **{interaction.guild.name}** has been **DENIED**\n**Reason: ** {reason}")


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
        
        # If time does not = the correct format, return
        if not re.match(LOARegFormat, time):
            return await ctx.send("Please use the correct time format: <number>y<number>m<number>w<number>d<number>h")

        # Find a record for the user and return if record is found
        loa_record = await loa.find_one({"user_id": ctx.author.id, "guild_id": ctx.guild.id})

        if loa_record:
            return await ctx.send("You have an ongoing LOA! End it to start a new one!")

        # Break time into y, m, w, d, h and find total days from that
        years, months, weeks, days, hours = extract_time_values(time)
        total_days = years * 365 + months * 30 + weeks * 7 + days

        # Find y, m, w, d, h from loa min and max
        min_years, min_months, min_weeks, min_days, _ = extract_time_values(loa_min)
        max_years, max_months, max_weeks, max_days, _ = extract_time_values(loa_max)

        # Find total days for loa min and max
        min_total_days = min_years * 365 + min_months * 30 + min_weeks * 7 + min_days
        max_total_days = max_years * 365 + max_months * 30 + max_weeks * 7 + max_days

        # Checks to see if the requested days is in between the min and max days
        if total_days < min_total_days:
            return await ctx.send("LOA time does not meet the minimum LOA time.")
        elif total_days > max_total_days:
            return await ctx.send("LOA time exceeds the maximum LOA time.")

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
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        items = await loa.find({'guild_id': ctx.guild.id}).to_list(length=None)
        view = PaginatorView(self.bot, ctx.author, items)
        embed = view.create_record_embed()

        await ctx.send(embed=embed, view=view, ephemeral=True)

    @loa.command(description="Manage a staff members LOA.")
    async def manage(self, ctx: commands.Context, user: discord.Member = None):
        if not user or user.id == ctx.author.id:
            member = ctx.author
        else:
            foundation_role = await ctx.guild.fetch_role(foundation_command)
            site_role = await ctx.guild.fetch_role(site_command)

            if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
                return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
            
            member = user

        active_loa = await loa.find_one({"user_id": member.id, "guild_id": ctx.guild.id})
        stored_loas = await stored_loa.find({"user_id": member.id, "guild_id": ctx.guild.id}).to_list(length=None)
        
        if not active_loa and stored_loas == []:
            return await ctx.send(f"{member.mention} has no LOA's to manage", ephemeral=True)

        des = ""

        des = "\n".join(
            [
                f"{discord.utils.format_dt(loa['start_date'])} - {discord.utils.format_dt(loa['end_date'])}"
                for loa in stored_loas
            ]
        )

        embed = discord.Embed(title="Leave Of Absence Admin Panel", description=f"LOA History {member.mention}:\n{des}")

        if not member.avatar.url:
            embed.set_author(icon_url=member.default_avatar.url, name=member.name)
        else:
            embed.set_author(icon_url=member.avatar.url, name=member.name)
        
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