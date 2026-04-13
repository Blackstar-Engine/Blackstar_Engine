import discord
from utils.constants import profiles

class EditProfileModal(discord.ui.Modal):
    def __init__(self, bot, profile: dict):
        self.bot = bot
        self.profile = profile

        super().__init__(title="Edit Your Profile")

        self.codename = discord.ui.TextInput(
            label="Codename",
            placeholder=str(profile.get('codename', "None"))[0:15],
            default=str(profile.get('codename', "None"))[0:15],
            required=True,
            max_length=25,
            style=discord.TextStyle.short
        )

        self.roblox_name = discord.ui.TextInput(
            label="Roblox Username",
            placeholder=str(profile.get('roblox_name', "None")),
            default=str(profile.get('roblox_name', "None")),
            required=True,
            max_length=32,
            style=discord.TextStyle.short
        )

        self.timezone = discord.ui.TextInput(
            label="Timezone",
            placeholder=str(profile.get('timezone', "None")),
            default=str(profile.get('timezone', "None")),
            required=True,
            max_length=10,
            style=discord.TextStyle.short
        )

        self.status = discord.ui.TextInput(
            label="Status (Active|Inactive|LOA|ROA|Retired)",
            placeholder=str(profile.get('status', "None")),
            default=str(profile.get('status', "None")),
            required=True,
            max_length=8,
            style=discord.TextStyle.short
        )

        self.add_item(self.codename)
        self.add_item(self.roblox_name)
        self.add_item(self.timezone)
        self.add_item(self.status)

    async def on_submit(self, interaction: discord.Interaction):
        r_name = self.roblox_name.value
        timezone = self.timezone.value
        codename = self.codename.value
        status = self.status.value

        if status.lower() not in ['active', 'inactive', 'loa', 'roa', 'retired']:
            embed = discord.Embed(title="Error", description="Please make sure the status is one of below:\n\n`Active`\n`Inactive`\n`LOA`\n`ROA`\n`retired`", color=discord.Color.light_grey())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await profiles.update_one({'user_id': self.profile.get("user_id", 0), 'guild_id': interaction.guild.id}, {'$set': {'roblox_name': r_name, 'timezone': timezone, 'codename': codename, 'status': status.title()}})

        edit_embed = discord.Embed(
                                title="Profile Edited!",
                                description=f"Your profile has been edited!\n\n**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Status: ** {status.title()}",
                                color=discord.Color.green()
                                )

        await interaction.response.send_message(embed=edit_embed, ephemeral=True)