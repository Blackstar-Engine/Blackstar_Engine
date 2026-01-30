import discord
from utils.ui.loa.modals.RequestDeny import RequestDenyModal
from utils.constants import loa_role, loa

class ExtendAcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, active_loa, new_end_date, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.User = user
        self.active_loa = active_loa
        self.new_end_date = new_end_date
        self.embed: discord.Embed = embed

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.title = "Extention Approved"
        self.embed.color = discord.Color.green()
        self.embed.add_field(name="Approved by", value=interaction.user.mention)

        await interaction.response.edit_message(embed=self.embed, view=None)

        await loa.update_one(self.active_loa, {'$set': {'end_date': self.new_end_date}})

        role = await interaction.guild.fetch_role(loa_role)

        await self.user.add_roles(role)
        await self.user.send(f"Your LOA time extention in **{interaction.guild.name}** has been **ACCEPTED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequestDenyModal(self.bot)
        await interaction.response.send_modal(modal)

        await modal.wait()

        reason = modal.reason.value

        self.embed.title = "Extention Denied"
        self.embed.color = discord.Color.red()
        self.embed.add_field(name="Denied Information", value=f"**Denied By: ** {interaction.user.mention}\n**Reason: ** {reason}")

        await interaction.edit_original_response(embed=self.embed, view=None)

        await self.user.send(f"Your LOA time extention in **{interaction.guild.name}** has been **DENIED**\n**Reason: ** {reason}")