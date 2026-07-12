import discord
from discord.ext import commands
from discord import ui
from ui.general.modals.CreateEmbed import CreateEmbedModal

class DMEmbedView(ui.View):
    def __init__(self, bot: commands.Bot, punished_user: discord.Member):
        super().__init__(timeout=None)
        self.bot = bot

        self.punished_user = punished_user

        self.button = discord.ui.Button(label="Create Embed", style=discord.ButtonStyle.primary, custom_id="create_embed")
        self.button.callback = self.create_embed_callback
        self.add_item(self.button)

    async def create_embed_callback(self, interaction: discord.Interaction):
        modal = CreateEmbedModal(self.bot, self.punished_user)
        await interaction.response.send_modal(modal)
