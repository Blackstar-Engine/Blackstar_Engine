import discord
from utils.constants import loa_role, loa
from ui.loa.modals.RequestDeny import RequestDenyModal

class RequestAcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, reason, start_date, end_date, time, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.User = user
        self.time = time
        self.reason = reason
        self.start_date = start_date
        self.end_date = end_date
        self.embed: discord.Embed = embed

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.title = "Leave Of Absence Approved"
        self.embed.color = discord.Color.green()
        self.embed.add_field(name="Approved by", value=interaction.user.mention)

        await interaction.response.edit_message(embed=self.embed, view=None)

        loa_doc = {
            "user_id": self.user.id,
            "guild_id": interaction.guild.id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days": self.time,
            "reason": self.reason,
            "moderator_id": interaction.user.id
        }
        await loa.insert_one(loa_doc)

        role = await interaction.guild.fetch_role(loa_role)

        await self.user.add_roles(role)
        await self.user.send(f"Your LOA in **{interaction.guild.name}** has been **ACCEPTED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequestDenyModal(self.bot)
        await interaction.response.send_modal(modal)

        await modal.wait()

        reason = modal.reason.value

        self.embed.title = "Leave Of Absence Denied"
        self.embed.color = discord.Color.red()
        self.embed.add_field(name="Denied Information", value=f"**Denied By: ** {interaction.user.mention}\n**Reason: ** {reason}")

        await interaction.edit_original_response(embed=self.embed, view=None)

        await self.user.send(f"Your LOA in **{interaction.guild.name}** has been **DENIED**\n**Reason: ** {reason}")