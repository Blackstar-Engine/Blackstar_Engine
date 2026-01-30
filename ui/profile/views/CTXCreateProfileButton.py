import discord
from ui.profile.modals.CreateProfile import CreateProfileModal

class CTXCreateProfileButton(discord.ui.View):
    def __init__(self, bot, user: discord.User):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="Create Profile", style=discord.ButtonStyle.green, custom_id="create_profile_button")
    async def create_profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Sorry but you can't use this button.", ephemeral=True)

        modal = CreateProfileModal(self.bot)
        await interaction.response.send_modal(modal)