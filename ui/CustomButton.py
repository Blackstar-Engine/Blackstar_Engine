import discord
from discord import ui


class CustomButton(ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle = discord.ButtonStyle.gray, row: int = 1, url: str = None, emoji = None, custom_id: str = None):
        super().__init__(style=style, label=label, row=row, url=url, emoji=emoji, custom_id=custom_id)
        self.status = False
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.status = True
        self.view.stop()
