import discord
from utils.constants import departments
from ui.manage_commands.views.DemoteRank import DemoteRankView
from utils.utils import fetch_department, fetch_unit_options

class DemoteUnitView(discord.ui.ActionRow):
    def __init__(self, profile):
        super().__init__()
        self.profile = profile

        options = fetch_unit_options(profile)

        self.unit_select = discord.ui.Select(
            placeholder="Select unit to demote",
            options=options,
            min_values=1,
            max_values=1
        )

        self.unit_select.callback = self.unit_select_callback

        self.add_item(self.unit_select)

    async def unit_select_callback(self, interaction: discord.Interaction):
        unit = self.unit_select.values[0]

        dept = await fetch_department(interaction, unit)
        if not dept:
            return

        current_rank = self.profile["unit"][unit]["rank"]
        ranks = dept.get("ranks", [])

        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"Selected Unit: {unit}\nCurrent Rank: {current_rank}"),
            discord.ui.TextDisplay("Select the new rank to demote to:"),
            DemoteRankView(self.profile, unit, ranks, current_rank),
            accent_color=discord.Color.yellow()
        )

        view.add_item(container)

        await interaction.response.edit_message(view=view)