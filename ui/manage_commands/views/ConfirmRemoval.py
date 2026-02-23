import discord
from discord.ui import View, Button

class ConfirmRemovalView(discord.ui.ActionRow):
    def __init__(self, bot, record, index):
        super().__init__()
        self.bot = bot
        self.record = record
        self.index = index
        self.status = None

        confirm_button = Button(label="Confirm", style=discord.ButtonStyle.green)
        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.red)

        confirm_button.callback = self.confirm
        cancel_button.callback = self.cancel

        self.add_item(confirm_button)
        self.add_item(cancel_button)

    async def confirm(self, interaction: discord.Interaction):
        self.status = 1

        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay('Deleting Profile...'),
            accent_color=discord.Color.green()
        )
        view.add_item(container)

        await interaction.response.edit_message(view=view)
        view.stop()
        self.view.stop()

    async def cancel(self, interaction: discord.Interaction):
        self.status = 0

        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay('Deletion Cancelled.'),
            accent_color=discord.Color.red()
        )
        view.add_item(container)

        await interaction.response.edit_message(view=view)
        view.stop()
        self.view.stop()