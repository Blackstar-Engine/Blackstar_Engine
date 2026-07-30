import discord
from discord.ext import commands
from discord import ui
from utils.utils import get_permission_node
from ui.ReasonModal import ReasonModal

class AcceptDenyButtons(ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, node_accept: str, node_deny: str, ask_reason: bool = True, **kwargs):
        super().__init__()
        self.bot = bot
        self.user = user
        self.node_accept = node_accept
        self.node_deny = node_deny
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
        if not await get_permission_node(interaction, self.node_accept):
            return
        
        await interaction.response.defer(ephemeral=True)

        self.is_accepted = True
        self.kwargs['moderator_obj'] = interaction.user

        self.view.stop()
    
    async def deny_callback(self, interaction: discord.Interaction):
        if not await get_permission_node(interaction, self.node_deny):
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
