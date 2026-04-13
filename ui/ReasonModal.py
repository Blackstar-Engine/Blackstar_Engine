import discord
from utils.utils import log_action

class ReasonModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Reason for Action")
        self.data = None

        self.reason = discord.ui.TextInput(
            label="Reason",
            required=True,
            style=discord.TextStyle.long
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        reason = self.reason.value

        self.data = reason
        
        self.stop()