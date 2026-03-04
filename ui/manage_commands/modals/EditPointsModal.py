import discord
from utils.constants import profiles

class EditPointsModal(discord.ui.Modal):
    def __init__(self, profile: dict, department):
        self.profile = profile
        self.department = department

        super().__init__(title="Edit Points")

        current_points = str(profile["unit"][department]["current_points"])
        total_points = str(profile["unit"][department]["total_points"])

        self.current = discord.ui.TextInput(
            label="Current Points",
            placeholder=current_points,
            default=current_points,
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.total = discord.ui.TextInput(
            label="Total Points",
            placeholder=total_points,
            default=total_points,
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.add_item(self.current)
        self.add_item(self.total)

    async def on_submit(self, interaction: discord.Interaction):
        current = float(self.current.value)
        total = float(self.total.value)

        await profiles.update_one({'user_id': self.profile["user_id"], 'guild_id': interaction.guild.id},
                                {'$set': {
                                        f"unit.{self.department}.current_points": current,
                                        f"unit.{self.department}.total_points": total,
                                    }
                                })

        self.profile["unit"][self.department]["current_points"] = current
        self.profile["unit"][self.department]["total_points"] = total

        edit_embed = discord.Embed(
                                title=f"{self.department} Points Changed!",
                                description=f"**Current Points:** {current}\n**Total Points:** {total}",
                                color=discord.Color.green()
                                )

        await interaction.response.send_message(embed=edit_embed, ephemeral=True)