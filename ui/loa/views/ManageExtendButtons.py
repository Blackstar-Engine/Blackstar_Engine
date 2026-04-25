import discord
from discord import ui
from discord.ext import commands
from ui.loa.modals.AddTime import AddTimeModal
from utils.constants import loa, stored_loa
from utils.utils import fetch_id
from ui.ReasonModal import ReasonModal
from utils.utils import interaction_check

class ManageExtendButton(ui.LayoutView):
    def __init__(self, bot: commands.Bot, user: discord.Member, member: discord.Member, active_loa: dict, description: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.member = member
        self.active_loa = active_loa
        self.description = description

        extend_button = ui.Button(label="Extend", style=discord.ButtonStyle.green)
        end_button = ui.Button(label="End", style=discord.ButtonStyle.red)
        extend_button.callback = self.manage_entend_button
        end_button.callback = self.manage_end_button

        action_row = ui.ActionRow(extend_button, end_button)

        container = ui.Container(
            ui.TextDisplay("## Leave Of Absence Admin Panel"),
            ui.TextDisplay(f"LOA History {member.mention}:\n{description}"), 
            accent_color=discord.Color.yellow()
        )
        if active_loa:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f"**Started:** {discord.utils.format_dt(active_loa.get("start_date"))}\n**Ending:** {discord.utils.format_dt(active_loa.get("end_date"))}\n**Reason:** ``{active_loa.get("reason")}``\n**Moderator:** <@{active_loa.get("moderator_id")}>"))
            container.add_item(ui.Separator())
            container.add_item(action_row)

        self.add_item(container)

    async def manage_entend_button(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        modal = AddTimeModal(self.bot, self.active_loa, self.user, self.member)
        await interaction.response.send_modal(modal)

    async def manage_end_button(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        modal = ReasonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        reason = modal.data

        results = await fetch_id(interaction.guild.id, ["loa_channel", "loa_role"])
        loa_channel = results["loa_channel"]
        loa_role = results["loa_role"]

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
            title="LOA Self Ended",
            description=f"**User: ** <@{self.active_loa.get("user_id")}>\n**Start Time: ** {discord.utils.format_dt(self.active_loa.get('start_date'))}\n**End Date: ** {discord.utils.format_dt(self.active_loa.get('end_date'))}\n**End Reason: ** {reason}",
            color=discord.Color.light_grey()
        )

        await channel.send(embed=log_embed)

        container = ui.Container(
            ui.TextDisplay("## Leave of Absence Ended"),
            ui.TextDisplay(f"You have successfully ended your LOA from {discord.utils.format_dt(self.active_loa.get('start_date'))} - {discord.utils.format_dt(self.active_loa.get('end_date'))}"),
            accent_color=discord.Color.green()
        )
        end_view = ui.LayoutView()
        end_view.add_item(container)

        await interaction.edit_original_response(view=end_view)
        