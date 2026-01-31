import discord
from utils.constants import profiles, overall_promotion_channel
from utils.utils import has_approval_perms
from ui.promotion.modals.PointsRemoval import PointsRemovalModal
from datetime import datetime
class PromotionRequestView(discord.ui.View):
    def __init__(self, bot, user: discord.Member, embed: discord.Embed, profile, department, new_rank):
        super().__init__(timeout=None)
        self.bot = bot
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
        
        modal = PointsRemovalModal(self.profile)
        await interaction.response.send_modal(modal)
        await modal.wait()

        points_to_remove = modal.data
        if points_to_remove is None:
            await interaction.followup.send("Promotion approval cancelled.", ephemeral=True)
            return
        
        
        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {
                "$set": {
                    f"unit.{self.department}.rank": self.new_rank
                },
                "$inc": {
                    f"unit.{self.department}.current_points": -float(points_to_remove)
                }
            }
        )

        self.embed.title = "Promotion Approved"
        self.embed.color = discord.Color.green()

        await interaction.message.edit(embed=self.embed, view=None)

        await self.user.send(f"Your Promotion to **{self.new_rank}** in **{interaction.guild.name}** has been **APPROVED**")

        channel: discord.TextChannel = self.bot.get_channel(overall_promotion_channel)
        user_profile: discord.Member = self.bot.get_user(self.profile.get("user_id"))
        if channel:
            embed = discord.Embed(title="New Promotion", description=f"**User: ** {user_profile.mention}\n**New Rank: ** {self.new_rank}\n**Department: ** {self.department}", color=discord.Color.green())
            embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")

            embed.set_thumbnail(url=user_profile.display_avatar.url)
            await channel.send(embed=embed)

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