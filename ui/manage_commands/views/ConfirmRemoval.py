import discord
from discord.ui import Button
from discord.ext import commands

class ConfirmRemovalView(discord.ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, moderator: discord.Member, nodes: dict):
        super().__init__()
        from ui.manage_commands.views.ReturnButton import ReturnButton
        self.bot = bot
        self.status = None
        self.nodes = nodes

        cancel_button = ReturnButton(bot, user, moderator, nodes)
        cancel_button.label = "Cancel"
        cancel_button.style = discord.ButtonStyle.red

        confirm_button = Button(label="Confirm", style=discord.ButtonStyle.green)

        confirm_button.callback = self.confirm

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