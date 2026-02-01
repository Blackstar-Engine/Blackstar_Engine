import discord
from utils.constants import departments
from ui.manage_commands.views.DemoteRank import DemoteRankView
from utils.utils import fetch_department, fetch_unit_options

class DemoteUnitView(discord.ui.View):
    def __init__(self, profile):
        super().__init__(timeout=120)
        self.profile = profile

        options = fetch_unit_options(profile)

        self.unit_select.options = options

    @discord.ui.select(placeholder="Select unit to demote", options=[])
    async def unit_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        unit = select.values[0]

        dept = await fetch_department(interaction, unit)
        if not dept:
            return

        current_rank = self.profile["unit"][unit]["rank"]
        ranks = dept.get("ranks", [])

        embed = discord.Embed(title="", description="Please select what rank you want to demote them to!", color=discord.Color.dark_embed())

        view = DemoteRankView(self.profile, unit, ranks, current_rank)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)