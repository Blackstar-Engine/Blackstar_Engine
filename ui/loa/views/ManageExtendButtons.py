import discord
from ui.loa.modals.AddTime import AddTimeModal
from ui.loa.modals.EndLOA import EndLOAModal
from utils.utils import interaction_check

class ManageExtendButton(discord.ui.View):
    def __init__(self, bot, user, member, document):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.member = member
        self.document = document

    @discord.ui.button(label="Extend", style=discord.ButtonStyle.green)
    async def manage_entend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)
        modal = AddTimeModal(self.bot, self.document, self.user, self.member)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="End", style=discord.ButtonStyle.red)
    async def manage_end_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)
        loa_end_modal = EndLOAModal(self.bot, self.user, self.member, self.document)
        await interaction.response.send_modal(loa_end_modal)