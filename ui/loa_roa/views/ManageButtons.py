import discord
from discord import ui
from discord.ext import commands
from utils.constants import loa, stored_loa, LOARegFormat
from utils.utils import fetch_id
from ui.ReasonModal import ReasonModal
from utils.utils import interaction_check
from ui.CustomModal import CustomModal
import re
from datetime import timedelta
from ui.AcceptDenyButtons import AcceptDenyButtons

class ManageExtendButton(ui.LayoutView):
    def __init__(self, bot: commands.Bot, user: discord.Member, abtype: str, member: discord.Member, active_loa: dict, description: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.abtype = abtype
        self.member = member
        self.active_loa = active_loa
        self.description = description

        extend_button = ui.Button(label="Extend", style=discord.ButtonStyle.green)
        end_button = ui.Button(label="End", style=discord.ButtonStyle.red)
        extend_button.callback = self.manage_entend_button
        end_button.callback = self.manage_end_button

        action_row = ui.ActionRow(extend_button, end_button)

        container = ui.Container(
            ui.TextDisplay(f"## {self.abtype.upper()} Management Panel"),
            ui.TextDisplay(f"{self.abtype.upper()} History {member.mention}:\n{description}"), 
            accent_color=discord.Color.light_grey()
        )
        if active_loa:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"**Started:** {discord.utils.format_dt(active_loa.get("start_date"))}\n"
                                              f"**Ending:** {discord.utils.format_dt(active_loa.get("end_date"))}\n"
                                              f"**Reason:** ``{active_loa.get("reason")}``\n"
                                              f"**Moderator:** <@{active_loa.get("moderator_id")}>"))
            container.add_item(ui.Separator())
            container.add_item(action_row)

        self.add_item(container)

    async def manage_entend_button(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        modal = CustomModal(
                    f"{self.abtype.upper()} Time Addition",
                    [
                        (
                            "time",
                            discord.ui.TextInput(
                                label="How Much Time",
                                placeholder="e.g. 2w, 4h, or 5d",
                                required=True,
                                row=1,
                                style=discord.TextStyle.short
                            )
                        ),
                        (
                            "reason",
                            discord.ui.TextInput(
                                label="Reason",
                                placeholder="I need more time",
                                required=True,
                                row=1,
                                style=discord.TextStyle.paragraph
                            )
                        )
                    ]
                )
        await interaction.response.send_modal(modal)

        await modal.wait()

        time_input_value = modal.time.value
        reason = modal.reason.value

        match = re.match(LOARegFormat, time_input_value)
        if not match:
            return await interaction.followup.send("Invalid time format. Use '1y2m3w4d5h' for a combination of years, months, weeks, days, and hours.")

        years, months, weeks, days, hours = map(int, match.groups(default="0"))
        time_delta = timedelta(days=years * 365 + months * 30 + weeks * 7 + days, hours=hours)

        new_end_date = self.active_loa["end_date"] + time_delta
        results = await fetch_id(interaction.guild.id, self.abtype)
        loa_channel = results["values"]["channel"]

        channel = await interaction.guild.fetch_channel(loa_channel)

        action_row = AcceptDenyButtons(bot=self.bot, user=interaction.user, node_accept=f"{self.abtype}.accept", node_deny=f"{self.abtype}.deny", ask_reason=True)
        container = ui.Container(
            ui.TextDisplay(f"## {self.abtype.upper()} Extension Requested"),
            ui.TextDisplay(f"**Member:** {self.member.mention}\n"
                            f"**Requested by:** {interaction.user.mention}\n"
                            f"**Old Ending:** {discord.utils.format_dt(self.active_loa['end_date'])}\n"
                            f"**New Ending:** {discord.utils.format_dt(new_end_date)}\n"
                            f"**Reason:** {reason}"),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.yellow()
        )
        view = ui.LayoutView()
        view.add_item(container)

        request_message = await channel.send(view=view)

        extend_embed = discord.Embed(
            title=f"{self.abtype.upper()} Extension Requested",
            description=f"New Requested Time: {discord.utils.format_dt(new_end_date)}",
            color=discord.Color.green()
        )

        await interaction.followup.send(embed=extend_embed, ephemeral=True)

        await view.wait()

        moderator_id = 0
        try:
            moderator_id = action_row.kwargs.get('moderator_obj', {}).id
        except Exception:
            pass

        if not action_row.is_accepted:
            status = "Denied"
        else:
            status = "Accepted"
            await loa.update_one(self.active_loa, {'$set': {'end_date': new_end_date}})

        status_container = ui.Container(
            ui.TextDisplay(f"## {self.abtype.upper()} Extension {status}"),
            ui.TextDisplay(f"**Member:** {self.member.mention}\n"
                            f"**Requested by:** {interaction.user.mention}\n"
                            f"**Old Ending:** {discord.utils.format_dt(self.active_loa['end_date'])}\n"
                            f"**New Ending:** {discord.utils.format_dt(new_end_date)}\n"
                            f"**Reason:** {reason}"),
            ui.Separator(),
            ui.TextDisplay(f"**{status} By: ** <@{moderator_id}>"),
            accent_color=(discord.Color.green() if status == "Accepted" else discord.Color.red())
        )

        try:
            view = ui.LayoutView()
            view.add_item(status_container)
            await request_message.edit(view=view)
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title=f"{self.abtype.upper()} Extension {status}",
            description=f"Your request to extend your {self.abtype.upper()} to {discord.utils.format_dt(new_end_date)} has been **{status}**.",
            color=discord.Color.green()
        )
        try:
            await self.user.send(embed=embed)
        except discord.Forbidden:
            pass

    async def manage_end_button(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        modal = ReasonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        reason = modal.data

        results = await fetch_id(interaction.guild.id, self.abtype)
        loa_channel = results["values"]["channel"]
        loa_role = results["values"]["role"]

        channel = await interaction.guild.fetch_channel(loa_channel)

        await stored_loa.insert_one(self.active_loa)
        await loa.delete_one(self.active_loa)
        try:
            await self.member.remove_roles(interaction.guild.get_role(loa_role))
        except discord.Forbidden:
            pass

        try:
            await self.member.edit(nick=self.active_loa.get("nickname", self.member.display_name))
        except discord.Forbidden:
            pass

        log_embed = discord.Embed(
            title=f"{self.abtype.upper()} Ended",
            description=f"**User: ** <@{self.active_loa.get("user_id")}>\n"
                        f"**Start Time: ** {discord.utils.format_dt(self.active_loa.get('start_date'))}\n"
                        f"**End Date: ** {discord.utils.format_dt(self.active_loa.get('end_date'))}\n"
                        f"**Reason: ** {reason}",
            color=discord.Color.light_grey()
        )

        await channel.send(embed=log_embed)

        container = ui.Container(
            ui.TextDisplay(f"### {self.abtype.upper()} Ended"),
            ui.TextDisplay(f"You have successfully ended your {self.abtype.upper()} from {discord.utils.format_dt(self.active_loa.get('start_date'))} - {discord.utils.format_dt(self.active_loa.get('end_date'))}"),
            accent_color=discord.Color.green()
        )
        end_view = ui.LayoutView()
        end_view.add_item(container)

        await interaction.edit_original_response(view=end_view)
        