import discord
from discord import ui
from utils.utils import fetch_department, has_approval_perms, log_action
from ui.PointsRemoval import PointsRemovalModal
from utils.constants import profiles
from ui.manage_commands.views.AdminTools import ManageDepartmentRow

class DepartmentButtons(ui.ActionRow):
    def __init__(self, bot, user, unit, profile):
        super().__init__()
        self.bot = bot
        self.user = user
        self.profile = profile
        self.unit = unit

        self.demote_button = ui.Button(label="Demote", style=discord.ButtonStyle.blurple)
        self.point_reduction = ui.Button(label="Reduce Points", style=discord.ButtonStyle.blurple)

        self.demote_button.callback = self._demote_button_callback
        self.point_reduction.callback = self._point_reduction_callback

        self.add_item(self.demote_button)
        self.add_item(self.point_reduction)

    async def _demote_button_callback(self, interaction: discord.Interaction):
        from ui.manage_commands.views.DemoteRank import DemoteRankView
        
        dept = await fetch_department(interaction, self.unit)
        if not dept:
            return
        
        from ui.manage_commands.views.ReturnButton import ReturnButton

        current_rank = self.profile["unit"][self.unit]["rank"]
        ranks = dept.get("ranks", [])

        view = discord.ui.LayoutView()
        action_row = discord.ui.ActionRow(ReturnButton(self.bot, self.user))
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"**Selected Unit:** {self.unit}\n**Current Rank:** {current_rank}"),
            discord.ui.Separator(),
            discord.ui.TextDisplay("Select the new rank to demote to:"),
            DemoteRankView(self.bot, self.user, self.profile, self.unit, ranks, current_rank),
            action_row,
            accent_color=discord.Color.yellow()
        )

        view.add_item(container)

        await interaction.response.edit_message(view=view)
    
    async def _point_reduction_callback(self, interaction: discord.Interaction):
        modal = PointsRemovalModal(self.profile)
        await interaction.response.send_modal(modal)

        await modal.wait()

        points = modal.data

        await log_action(ctx=interaction, log_type="point_deduction", user_id=self.user.id, points=points, command_name="manage profile")

        await profiles.update_one({"guild_id": interaction.guild.id, "user_id": self.user.id}, {"$inc": {f"unit.{self.unit}.current_points": -float(points)}})

        confirm_view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay(f"✅ **{points} points have been deducted!**"),
            accent_color=discord.Color.green()
        )
        confirm_view.add_item(container)
        await interaction.followup.send(view=confirm_view, ephemeral=True)

        self.profile["unit"][self.unit]["current_points"] += -float(points)

        department = self.profile["unit"][self.unit]

        main_view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {self.unit} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(self.bot, self.user, self.unit, self.profile),
            accent_color=discord.Color.light_grey()
        )

        if (
            await self.bot.is_owner(interaction.user)
            or await has_approval_perms(self.user, 6)
        ):
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.profile, self.unit))

        main_view.add_item(container)

        await interaction.edit_original_response(view=main_view)

