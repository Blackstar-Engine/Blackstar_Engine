import discord
from utils.constants import profiles
from utils.utils import has_approval_perms

class PromotionRequestView(discord.ui.View):
    def __init__(self, user: discord.Member, embed: discord.Embed, profile, department, new_rank):
        super().__init__(timeout=None)
        self.user = user
        self.embed = embed
        self.profile = profile
        self.department = department
        self.new_rank = new_rank

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not has_approval_perms(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to approve promotions.",
                ephemeral=True
            )
            return
        
        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {
                "$set": {
                    f"unit.{self.department}.rank": self.new_rank
                },
            }
        )

        self.embed.title = "Promotion Approved"
        self.embed.color = discord.Color.green()

        await interaction.message.edit(embed=self.embed, view=None)

        await self.user.send(f"Your Promotion to **{self.new_rank}** in **{interaction.guild.name}** has been **APPROVED**")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not has_approval_perms(interaction.user):
            await interaction.response.send_message(
                "You do not have permission to deny promotions.",
                ephemeral=True
            )
            return

        self.embed.title = "Promotion Denied"
        self.embed.color = discord.Color.red()

        await interaction.message.edit(embed=self.embed, view=None)

        await self.user.send(f"Your Promotion to **{self.new_rank}** in **{interaction.guild.name}** has been **DENIED**")