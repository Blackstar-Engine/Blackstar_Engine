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
            max_length=10,
            style=discord.TextStyle.short
        )
        self.add_item(self.points)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            points = float(self.points.value)
        except ValueError:
            return await interaction.followup.send("Please enter a valid number for points.", ephemeral=True)
        
        if points <= 0:
            return await interaction.followup.send("Points to remove must be greater than zero.", ephemeral=True)

        await log_action(ctx=interaction, log_type="point_deduction", user_id=self.profile["user_id"], points=points, command_name="promotion request/manage profile")

        self.data = points
        
        self.stop()