import discord
import re
from datetime import timedelta
from utils.constants import loa_channel, LOARegFormat, loa
from ui.loa.views.ExtendAcceptDenyButtons import ExtendAcceptDenyButtons

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