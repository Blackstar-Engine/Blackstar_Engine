import discord
from discord.ext import commands
from discord import ui
from ui.manage_commands.modals.EditPointsModal import EditPointsModal
from utils.utils import fetch_department
from utils.constants import profiles

class ChangeRankRow(ui.ActionRow):
    def __init__(self, profile, options, department):
        super().__init__()
        self.profile = profile
        self.options = options
        self.department = department

        self.unit_select = ui.Select(placeholder="None Selected", min_values=1, max_values=1, options=options)
        self.unit_select.callback = self._unit_callback

        self.add_item(self.unit_select)

    async def _unit_callback(self, interaction: discord.Interaction):
        selection = self.unit_select.values[0]

        await profiles.update_one(
            {'user_id': interaction.user.id, 'guild_id': self.profile["user_id"]},
            {"$set": {
                f"unit.{self.department}.rank": selection
            }}
        )

        self.profile["unit"][self.department]["rank"] = selection

        embed = discord.Embed(title=f"{self.department} Rank Changed!", 
                              description=f"**New Rank: **{selection}",
                              color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.view.stop()

class ManageDepartmentRow(ui.ActionRow):
    def __init__(self, profile, department):
        super().__init__()
        self.profile = profile
        self.department = department

        change_role_button = ui.Button(label="Change Role", style=discord.ButtonStyle.grey)
        edit_points_button = ui.Button(label="Edit points", style=discord.ButtonStyle.grey)

        change_role_button.callback = self._change_button_callback
        edit_points_button.callback = self._edit_points_callback

        self.add_item(change_role_button)
        self.add_item(edit_points_button)
    
    async def _change_button_callback(self, interaction: discord.Interaction):
        department_doc = await fetch_department(interaction, self.department)
        options = []
        for rank in department_doc.get("ranks"):
            options.append(discord.SelectOption(label=rank.get("name")))

        action_row = ChangeRankRow(self.profile, options, self.department)
        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay("## Select a Unit"),
            ui.TextDisplay("Please select this users new rank"),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )
        view.add_item(container)

        await interaction.response.send_message(view=view, ephemeral=True)

        await view.wait()

        self.profile = action_row.profile
    
    async def _edit_points_callback(self, interaction: discord.Interaction):
        modal = EditPointsModal(self.profile, self.department)
        await interaction.response.send_modal(modal)

        await modal.wait()

        self.profile = modal.profile
