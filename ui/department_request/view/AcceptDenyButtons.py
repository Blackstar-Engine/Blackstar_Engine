import discord
from discord.ext import commands
from utils.constants import site_command, foundation_command, profiles

class AcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, embed, department):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed: discord.Embed = embed
        self.user: discord.Member = user
        self.department = department

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id="department_accept_button"
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        site_role = interaction.guild.get_role(site_command)
        foundation_role = interaction.guild.get_role(foundation_command)

        if foundation_role not in interaction.user.roles and site_role not in interaction.user.roles:
            return await interaction.response.send_message("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        profile = await profiles.find_one({"guild_id": interaction.guild.id, "user_id": self.user.id})
        if profile.get("unit") == []:
            profile["unit"] = {}
        
        unit_key = self.department["display_name"]
        unit_data = profile.get("unit", {}).get(unit_key)

        if unit_data is None:
            await profiles.update_one(
                {"_id": profile["_id"]},
                {
                    '$set': {
                        f"unit.{unit_key}": {
                            'rank': self.department["ranks"][0]["name"],
                            'is_active': True,
                            'current_points': 0,
                            'total_points': 0,
                            'subunits': []
                        },
                    }
                }
            )
        elif unit_data.get("is_active") is False:
            unit_data["is_active"] = True

            await profiles.update_one(
                {"_id": profile["_id"]},
                {
                    '$set': {
                        f"unit.{unit_key}": 
                            unit_data
                        ,
                    }
                }
            )
        else:
            raise commands.CommandInvokeError("Failed to add unit to department request")

        self.embed.color = discord.Color.green()
        self.embed.title = "Enlistment Accepted"

        await self.user.send(
            f"Your department request for **{self.department["display_name"]}** "
            f"in **{interaction.guild.name}** has been **ACCEPTED**!"
        )

        await interaction.response.edit_message(
            content=None,
            view=None,
            embed=self.embed
        )

        self.stop()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="department_deny_button")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        site_role = interaction.guild.get_role(site_command)
        foundation_role = interaction.guild.get_role(foundation_command)

        if foundation_role not in interaction.user.roles and site_role not in interaction.user.roles:
            return await interaction.response.send_message("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        self.embed.color = discord.Color.red()
        self.embed.title = "Enlistment Denied"
        
        await self.user.send(f"Your department request for **{self.department["display_name"]}** in **{interaction.guild.name}** has been **DENIED**!")
        await interaction.response.edit_message(content=None, view=None, embed=self.embed)

        self.stop()