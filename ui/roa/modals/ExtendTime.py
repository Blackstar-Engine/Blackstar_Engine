import discord
from discord import ui
from discord.ext import commands
import re
from datetime import timedelta
from utils.constants import LOARegFormat, roa
from ui.AcceptDenyButtons import AcceptDenyButtons
from utils.utils import fetch_id

class AddTimeModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, active_roa: dict, user: discord.Member, member: discord.Member):
        super().__init__(title="ROA Time Addition")
        self.bot = bot
        self.active_roa = active_roa
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

        new_end_date = self.active_roa["end_date"] + time_delta
        results = await fetch_id(interaction.guild.id, ["loa_channel"])
        loa_channel = results["loa_channel"]

        if self.member == self.user:  # If managing your own ROA
            channel = await interaction.guild.fetch_channel(loa_channel)

            action_row = AcceptDenyButtons(bot = self.bot, user=interaction.user, permission_level=3)
            container = ui.Container(
                ui.TextDisplay("## ROA Extension Requested"),
                ui.TextDisplay(f"**Member:** {self.member.mention}\n**Requested by:** {interaction.user.mention}\n**New End Date:** {discord.utils.format_dt(new_end_date)}\n**Reason:** {reason}"),
                ui.Separator(),
                action_row,
                accent_color=discord.Color.yellow()
            )
            view = ui.LayoutView()
            view.add_item(container)

            request_message = await channel.send(view=view)

            extend_embed = discord.Embed(
                title="ROA Extention",
                description=f"Successfully sent the request. The ROA will end at {discord.utils.format_dt(new_end_date)}",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=extend_embed, ephemeral=True)

            await view.wait()

            if not action_row.is_accepted:
                try:
                    embed = discord.Embed(
                        title="ROA Extension Denied",
                        description=f"Your request to extend your ROA to {discord.utils.format_dt(new_end_date)} has been **DENIED**.\n**Reason: ** {action_row.kwargs.get('reason', 'No reason provided.')} ",
                        color=discord.Color.red()
                    )
                    await self.user.send(embed=embed)

                    container = ui.Container(
                        ui.TextDisplay("## ROA Extension Denied"),
                        ui.TextDisplay(f"**Member:** {self.member.mention}\n**Requested by:** {interaction.user.mention}\n**New End Date:** {discord.utils.format_dt(new_end_date)}\n**Reason:** {reason}"),
                        ui.Separator(),
                        ui.TextDisplay(f"**Denied By: ** {interaction.user.mention}\n**Reason: ** {action_row.kwargs.get('reason', 'No reason provided.')}"),
                        accent_color=discord.Color.red()
                    )
                    view = ui.LayoutView()
                    view.add_item(container)

                    await request_message.edit(view=view)
                except discord.Forbidden:
                    pass
            else:
                await roa.update_one(self.active_roa, {'$set': {'end_date': new_end_date}})

                try:
                    embed = discord.Embed(
                        title="ROA Extension Accepted",
                        description=f"Your request to extend your ROA to {discord.utils.format_dt(new_end_date)} has been **ACCEPTED**.",
                        color=discord.Color.green()
                    )
                    await self.user.send(embed=embed)

                    container = ui.Container(
                        ui.TextDisplay("## ROA Extension Accepted"),
                        ui.TextDisplay(f"**Member:** {self.member.mention}\n**Requested by:** {interaction.user.mention}\n**New End Date:** {discord.utils.format_dt(new_end_date)}\n**Reason:** {reason}"),
                        ui.Separator(),
                        ui.TextDisplay(f"**Accepted By: ** {interaction.user.mention}"),
                        accent_color=discord.Color.green()
                    )
                    view = ui.LayoutView()
                    view.add_item(container)

                    await request_message.edit(view=view)
                except discord.Forbidden:
                    pass

                

        else:  # If managing someone else's ROA
            await roa.update_one(self.active_roa, {'$set': {'end_date': new_end_date}})

            channel = await interaction.guild.fetch_channel(loa_channel)

            log_embed = discord.Embed(
                title="ROA Extended By Moderator",
                description=f"**User: ** <@{self.active_roa.get("user_id")}>\n**Start Time: ** {self.active_roa.get('start_date')}\n**End Date: ** {new_end_date}\n**End Reason: ** {reason}",
                color=discord.Color.light_grey()
            )

            await channel.send(embed=log_embed)

            extend_embed = discord.Embed(
                title="ROA Extention",
                description=f"Successfully extended {self.member.mention}'s ROA. The ROA will end at {discord.utils.format_dt(new_end_date)}",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=extend_embed, ephemeral=True)