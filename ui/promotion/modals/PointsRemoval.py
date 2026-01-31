import discord
from utils.constants import profiles

class PointsRemovalModal(discord.ui.Modal):
    def __init__(self, profile):
        super().__init__(title="Promotion Points Removal")
        self.profile = profile
        self.data = None

        self.points = discord.ui.TextInput(
            label="Points to Remove",
            placeholder="1",
            required=True,
            row=1,
            max_length=3,
            style=discord.TextStyle.short
        )
        self.add_item(self.points)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        points = self.points.value

        self.data = points
        
        self.stop()