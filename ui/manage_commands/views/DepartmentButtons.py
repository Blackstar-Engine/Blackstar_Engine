import discord
from discord.ext import commands
from discord import ui
from utils.utils import fetch_department, get_permission_node, log_action
from ui.PointsRemoval import PointsRemovalModal
from utils.constants import profiles
from ui.manage_commands.views.AdminTools import ManageDepartmentRow

class DepartmentButtons(ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, moderator: discord.Member, user_profile: dict, unit: str, is_owner: bool, nodes: dict):
        super().__init__()
        self.bot = bot
        self.moderator = moderator
        self.user = user
        self.user_profile = user_profile
        self.unit = unit
        self.is_owner = is_owner
        self.nodes = nodes
        self.node_admin = nodes.get("admin")

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

        current_rank = self.user_profile["unit"][self.unit]["rank"]
        ranks = dept.get("ranks", [])

        view = discord.ui.LayoutView()
        action_row = discord.ui.ActionRow(ReturnButton(self.bot, self.user, self.moderator, self.nodes))
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"**Selected Unit:** {self.unit}\n**Current Rank:** {current_rank}"),
            discord.ui.Separator(),
            discord.ui.TextDisplay("Select the new rank to demote to:"),
            DemoteRankView(bot=self.bot,
                           user=self.user,
                           moderator=self.moderator,
                           user_profile=self.user_profile,
                           unit=self.unit, 
                           ranks=ranks, 
                           current_rank=current_rank,
                           nodes=self.nodes,
                           is_owner=self.is_owner),
            action_row,
            accent_color=discord.Color.yellow()
        )

        view.add_item(container)

        await interaction.response.edit_message(view=view)
    
    async def _point_reduction_callback(self, interaction: discord.Interaction):
        modal = PointsRemovalModal(self.user_profile)
        await interaction.response.send_modal(modal)

        await modal.wait()

        points = modal.data

        current_points = self.user_profile["units"][self.unit]["current_points"]
        if current_points <= 0:
            return await interaction.followup.send("This users current points are already 0 or below, sorry you can reduce points", ephemeral=True)

        await log_action(ctx=interaction, log_type="point_deduction", user_id=self.moderator.id, points=points, command_name="manage profile")

        await profiles.update_one({"guild_id": interaction.guild.id, "user_id": self.user.id}, {"$inc": {f"unit.{self.unit}.current_points": -float(points)}})

        confirm_view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay(f"✅ **{points} points have been deducted!**"),
            accent_color=discord.Color.green()
        )
        confirm_view.add_item(container)
        await interaction.followup.send(view=confirm_view, ephemeral=True)

        self.user_profile["unit"][self.unit]["current_points"] += -float(points)

        department = self.user_profile["unit"][self.unit]

        main_view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {self.unit} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(bot=self.bot,
                              user=self.user,
                              moderator=self.moderator,
                              user_profile=self.user_profile,
                              unit=self.unit,
                              is_owner=self.is_owner,
                              nodes=self.nodes),
            accent_color=discord.Color.light_grey()
        )

        if self.is_owner or self.node_admin:
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.user_profile, self.unit))

        main_view.add_item(container)

        await interaction.edit_original_response(view=main_view)

