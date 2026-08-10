import discord
from discord import ui


class CustomButton(ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle = discord.ButtonStyle.gray, row: int = 1, url: str = None, emoji = None, custom_id: str = None, auto_defer: bool = True):
        super().__init__(style=style, label=label, row=row, url=url, emoji=emoji, custom_id=custom_id)
        self.status = False
        self.clicked_interaction = None
        self.auto_defer = auto_defer
    
    async def callback(self, interaction: discord.Interaction):
        # store the interaction from the button click so callers can use it
        self.clicked_interaction = interaction
        if self.auto_defer:
            await interaction.response.defer(ephemeral=True)
        self.status = True
        self.view.stop()
