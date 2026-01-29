import discord
from utils.constants import profiles

class EditProfileModal(discord.ui.Modal):
    def __init__(self, bot, profile: dict, embed: discord.Embed):
        self.bot = bot
        self.profile = profile
        self.embed = embed

        super().__init__(title="Edit Your Profile")

        self.codename = discord.ui.TextInput(
            label="Codename",
            placeholder=profile.get('codename'),
            default=profile.get('codename'),
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.roblox_name = discord.ui.TextInput(
            label="Roblox Username",
            placeholder=profile.get('roblox_name'),
            default=profile.get('roblox_name'),
            required=True,
            max_length=32,
            style=discord.TextStyle.short
        )

        self.timezone = discord.ui.TextInput(
            label="Timezone",
            placeholder=profile.get('timezone'),
            default=profile.get('timezone'),
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.status = discord.ui.TextInput(
            label="Status (Active or Inactive)",
            placeholder=profile.get('status'),
            default=profile.get('status'),
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

        if status.lower() not in ['active', 'inactive']:
            await interaction.response.send_message("Status must be either 'Active' or 'Inactive'. Please try again.", ephemeral=True)
            return

        await profiles.update_one({'user_id': interaction.user.id, 'guild_id': interaction.guild.id}, {'$set': {'roblox_name': r_name, 'timezone': timezone, 'codename': codename, 'status': status.title()}})

        edit_embed = discord.Embed(
                                title="Profile Edited!",
                                description=f"Your profile has been edited!\n\n**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Status: ** {status.title()}",
                                color=discord.Color.green()
                                )
        
        self.embed.description = f"**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Rank: ** {self.profile.get('rank')}\n**Unit(s): **{', '.join(self.profile.get('unit', []))}\n**Private Unit(s): **{', '.join(self.profile.get('private_unit', []))}\n**Join Date: ** {self.profile.get('join_date')}\n**Status: ** {status.title()}"

        await interaction.response.edit_message(embed=self.embed)
        await interaction.followup.send(embed=edit_embed, ephemeral=True)