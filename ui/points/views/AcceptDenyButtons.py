import discord
from utils.constants import ia_id, central_command, high_command, site_command, foundation_command, wolf_id, profiles

class AcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, points, embed, profile, dept):
        super().__init__(timeout=None)
        self.bot = bot
        self.points = points
        self.embed: discord.Embed = embed
        self.profile = profile
        self.user: discord.Member = user
        self.dept = dept

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="points_accept_button"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        ia_role = interaction.guild.get_role(ia_id)
        central_role = interaction.guild.get_role(central_command)
        high_role = interaction.guild.get_role(high_command)
        site_role = interaction.guild.get_role(site_command)
        foundation_role = interaction.guild.get_role(foundation_command)

        if interaction.user.id != wolf_id:

            if 1 <= self.points <= 1.5:
                allowed_roles = [
                    ia_role,
                    central_role,
                    high_role,
                    site_role,
                    foundation_role
                ]

            elif 1.5 < self.points <= 2:
                allowed_roles = [
                    central_role,
                    high_role,
                    site_role,
                    foundation_role
                ]

            elif 2 < self.points <= 7.99:
                allowed_roles = [
                    site_role,
                    foundation_role
                ]

            elif self.points >= 8:
                allowed_roles = [
                    foundation_role
                ]

            else:
                allowed_roles = []

            allowed_roles = [r for r in allowed_roles if r is not None]

            if not any(role in interaction.user.roles for role in allowed_roles):
                await interaction.response.send_message(
                    "❌ You do not have permission to accept this point request.",
                    ephemeral=True
                )
                return
            
        await profiles.update_one(
            self.profile,
            {'$inc': {
                f"unit.{self.dept}.current_points": self.points,
                f"unit.{self.dept}.total_points": self.points
            }}
        )

        self.embed.color = discord.Color.green()
        self.embed.title = "Points Accepted"
        self.embed.add_field(name="Moderator", value=f"{interaction.user.mention}", inline=False)

        await self.user.send(
            f"Your points request for **{self.points}** "
            f"in **{interaction.guild.name}** has been **ACCEPTED**!"
        )

        await interaction.response.edit_message(
            content=None,
            view=None,
            embed=self.embed
        )

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="points_deny_button")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.embed.color = discord.Color.red()
        self.embed.title = "Points Denied"
        self.embed.add_field(name="Moderator", value=f"{interaction.user.mention}", inline=False)
        
        await self.user.send(f"Your points request for **{self.points}** in **{interaction.guild.name}** has been **DENIED**!")
        await interaction.response.edit_message(content=None, view=None, embed=self.embed)