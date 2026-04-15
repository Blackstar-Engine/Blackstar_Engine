import discord
from utils.utils import log_action

class PointsRemovalModal(discord.ui.Modal):
    def __init__(self, profile):
        super().__init__(title="Points Deduction")
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
        if not points.isdigit() or int(points) <= 0:
            await interaction.followup.send("Please enter a valid positive integer for points.", ephemeral=True)
            return

        await log_action(ctx=interaction, log_type="point_deduction", user_id=self.profile["user_id"], points=points)

        self.data = points
        
        self.stop()