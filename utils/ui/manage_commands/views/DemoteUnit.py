import discord
from utils.constants import departments
from utils.ui.manage_commands.views.DemoteRank import DemoteRankView

class DemoteUnitView(discord.ui.View):
    def __init__(self, profile):
        super().__init__(timeout=120)
        self.profile = profile

        options = [
            discord.SelectOption(label=unit)
            for unit, data in profile.get("unit", {}).items()
            if data.get("is_active")
        ]

        self.unit_select.options = options

    @discord.ui.select(placeholder="Select unit to demote", options=[])
    async def unit_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        unit = select.values[0]

        dept = await departments.find_one({"display_name": unit})
        if not dept:
            await interaction.response.send_message("Department not found.", ephemeral=True)
            return

        current_rank = self.profile["unit"][unit]["rank"]

        await interaction.response.send_message(
            view=DemoteRankView(
                profile=self.profile,
                unit=unit,
                ranks=dept.get("ranks", []),
                current_rank=current_rank
            ),
            ephemeral=True
        )