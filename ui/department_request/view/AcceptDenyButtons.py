import discord
from discord.ext import commands
from utils.constants import site_command, foundation_command, profiles, central_command, high_command
from discord import ui

class DeptRequestButtons(ui.ActionRow):
    def __init__(self):
        super().__init__()

        accept_button = ui.Button(label="Accept", style=discord.ButtonStyle.green, custom_id="department_accept_button", row=1)
        deny_button = ui.Button(label="Deny", style=discord.ButtonStyle.red, custom_id="department_deny_button", row=1)

        accept_button.callback = self.accept_callback
        deny_button.callback = self.deny_callback

        self.add_item(accept_button)
        self.add_item(deny_button)
    
    async def deny_callback(self, interaction: discord.Interaction):
        site_role = interaction.guild.get_role(site_command)
        foundation_role = interaction.guild.get_role(foundation_command)
        central_role = interaction.guild.get_role(central_command)
        high_role = interaction.guild.get_role(high_command)

        if foundation_role not in interaction.user.roles and site_role not in interaction.user.roles and central_role not in interaction.user.roles and high_role not in interaction.user.roles:
            return await interaction.response.send_message("You need to be apart of either foundation, site, central, or high command to manage another user", ephemeral=True)
        
        
        profile = await profiles.find_one({"guild_id": interaction.guild.id, "user_id": self.view.user.id})
        
        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('## Enlistment Denied'),
            ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: ** {profile.get('roblox_name')}\n**Status: ** {profile.get('status')}\n**Join Date: ** {profile.get('join_date')}\n**Time Zone: **{profile.get('timezone')}\n**Moderator: ** {interaction.user.mention}"),
            accent_color=discord.Color.red()
        )
        view.add_item(container)

        await self.view.user.send(f"Your department request for **{self.view.department["display_name"]}** in **{interaction.guild.name}** has been **DENIED**!")
        await interaction.response.edit_message(view=view)

        self.view.stop()
        view.stop()

    async def accept_callback(self, interaction: discord.Interaction):
        site_role = interaction.guild.get_role(site_command)
        foundation_role = interaction.guild.get_role(foundation_command)
        central_role = interaction.guild.get_role(central_command)
        high_role = interaction.guild.get_role(high_command)

        if foundation_role not in interaction.user.roles and site_role not in interaction.user.roles and central_role not in interaction.user.roles and high_role not in interaction.user.roles:
            return await interaction.response.send_message("You need to be apart of either foundation, site, central, or high command to manage another user", ephemeral=True)
        
        profile = await profiles.find_one({"guild_id": interaction.guild.id, "user_id": self.view.user.id})
        if profile.get("unit") == []:
            profile["unit"] = {}
        
        unit_key = self.view.department["display_name"]
        unit_data = profile.get("unit", {}).get(unit_key)

        if unit_data is None:
            await profiles.update_one(
                {"_id": profile["_id"]},
                {
                    '$set': {
                        f"unit.{unit_key}": {
                            'rank': self.view.department["ranks"][0]["name"],
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

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('## Enlistment Accepted'),
            ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: ** {profile.get('roblox_name')}\n**Status: ** {profile.get('status')}\n**Join Date: ** {profile.get('join_date')}\n**Time Zone: **{profile.get('timezone')}\n**Moderator: ** {interaction.user.mention}"),
            accent_color=discord.Color.green()
        )
        view.add_item(container)

        await self.view.user.send(
            f"Your department request for **{self.view.department['display_name']}** "
            f"in **{interaction.guild.name}** has been **ACCEPTED**!"
        )

        await interaction.response.edit_message(view=view)

        self.view.stop()
        view.stop()

class AcceptDenyButtons(ui.LayoutView):
    def __init__(self, bot, user, department, profile):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.Member = user
        self.profile = profile
        self.department = department

        container = ui.Container(
            ui.TextDisplay('## Enlistment Request'),
            ui.TextDisplay(f"**Department: **{department.get('display_name')}\n**Codename: **{self.profile.get('codename')}\n**Roblox Name: ** {self.profile.get('roblox_name')}\n**Status: ** {self.profile.get('status')}\n**Join Date: ** {self.profile.get('join_date')}\n**Time Zone: **{self.profile.get('timezone')}"),
            ui.Separator(),
            DeptRequestButtons(),
            accent_color=discord.Color.yellow()
        )

        self.add_item(container)