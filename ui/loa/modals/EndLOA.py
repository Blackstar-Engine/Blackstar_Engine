import discord
from utils.constants import loa_channel, stored_loa, loa

class EndLOAModal(discord.ui.Modal):
    def __init__(self, bot, user, member, active_loa):
        super().__init__(title="Provide a Reason")
        self.bot = bot
        self.user = user
        self.member = member
        self.active_loa = active_loa

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Because i said so!",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value

        channel = await interaction.guild.fetch_channel(loa_channel)

        await stored_loa.insert_one(self.active_loa)
        await loa.delete_one(self.active_loa)

        log_embed = discord.Embed(
            title="LOA Ended",
            description=f"**User: ** <@{self.active_loa.get("user_id")}>\n**Start Time: ** {discord.utils.format_dt(self.active_loa.get('start_date'))}\n**End Date: ** {discord.utils.format_dt(self.active_loa.get('end_date'))}\n**End Reason: ** {reason}",
            color=discord.Color.light_grey()
        )

        await channel.send(embed=log_embed)

        embed = discord.Embed(
            title="Leave of Absence Ended",
            description=f"You have successfully ended your LOA from {discord.utils.format_dt(self.active_loa.get('start_date'))} - {discord.utils.format_dt(self.active_loa.get('end_date'))}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)