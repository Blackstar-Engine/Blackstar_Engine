import discord
from discord import ui

class DeptSelect(ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Select a Unit",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]

        self.values.clear()
        await interaction.response.edit_message(view=self.view)

        if value == "no_units":
            await interaction.followup.send("You are not currently enlisted in any units.", ephemeral=True)
            return
        
        department = self.view.profile["unit"][value]

        embed = discord.Embed(
            title="Unit Information",
            description=f"**Unit Name: ** {value}\n**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}",
            color=discord.Color.light_grey()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

class UnitSelectView(ui.LayoutView):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

        action_row = ui.ActionRow(DeptSelect(options))
        private_unit = ", ".join(profile.get('private_unit', []))

        container = ui.Container(
            ui.TextDisplay('## Profile Information'),
            action_row,
            ui.Separator(),
            ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}"),
            ui.Separator(),
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)
    
    