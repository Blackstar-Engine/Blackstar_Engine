import discord
from discord.ext import commands
from discord import ui
from utils.utils import has_approval_perms
from ui.ReasonModal import ReasonModal

class AcceptDenyButtons(ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, permission_level: int = 3, ask_reason: bool = True, **kwargs):
        super().__init__()
        self.bot = bot
        self.user = user
        self.permission_level = permission_level
        self.ask_reason = ask_reason
        self.kwargs = kwargs

        self.is_accepted = None

        accept_button = ui.Button(label="Accept", style=discord.ButtonStyle.green)
        deny_button = ui.Button(label="Deny", style=discord.ButtonStyle.red)

        accept_button.callback = self.accept_callback
        deny_button.callback = self.deny_callback

        self.add_item(accept_button)
        self.add_item(deny_button)

    
    async def accept_callback(self, interaction: discord.Interaction):
        if not await has_approval_perms(interaction, self.permission_level):
            return
        
        await interaction.response.defer(ephemeral=True)

        self.is_accepted = True
        self.kwargs['moderator_obj'] = interaction.user

        self.view.stop()
    
    async def deny_callback(self, interaction: discord.Interaction):
        if not await has_approval_perms(interaction, self.permission_level):
            return
        
        if self.ask_reason:
            modal = ReasonModal()
            await interaction.response.send_modal(modal)

            await modal.wait()

            reason = modal.data

            self.kwargs['reason'] = reason
        else:
            self.kwargs['reason'] = 'No reason provided.'

            await interaction.response.defer(ephemeral=True)

        self.is_accepted = False
        self.kwargs['moderator_obj'] = interaction.user

        self.view.stop()
