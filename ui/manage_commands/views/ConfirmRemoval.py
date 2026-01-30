import discord
from discord.ui import View, Button

class ConfirmRemovalView(View):
    def __init__(self, bot, record, index):
        super().__init__()
        self.bot = bot
        self.record = record
        self.index = index

        self.status = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.status = 1

        embed = discord.Embed(
            title="Record Removed",
            description="The fire record has been successfully removed.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.status = 0
        embed = discord.Embed(
            title="Removal Cancelled",
            description="The removal of the fire record has been cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()