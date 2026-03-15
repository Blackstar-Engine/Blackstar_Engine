import discord
from discord import ui

class PointsRoleSelect(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Select a Role",
                        min_values=1,
                        max_values=1,
                        options=options)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        value = self.values[0]

        if value == "no_units":
            self.view.dept = "no_unit"
        else:
            self.view.dept = value

        self.view.stop()

class UnitSelectView(discord.ui.LayoutView):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

        self.dept = None

        action_row = ui.ActionRow(PointsRoleSelect(options))

        container = ui.Container(
            ui.TextDisplay('## Unit Selection'),
            ui.TextDisplay('Please select a unit to proceed.'),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)