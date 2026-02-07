import discord
import datetime
from utils.constants import profiles
from datetime import datetime
from utils.utils import profile_creation_embed

class CreateProfileModal(discord.ui.Modal):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(title="Create Your Profile")

        self.codename = discord.ui.TextInput(
            label="Codename",
            placeholder="Create a codename for yourself",
            required=True,
            max_length=32,
            style=discord.TextStyle.short
        )

        self.roblox_name = discord.ui.TextInput(
            label="Roblox Username",
            placeholder="Enter Your Roblox Username",
            required=True,
            max_length=32,
            style=discord.TextStyle.short
        )

        self.timezone = discord.ui.TextInput(
            label="Timezone",
            placeholder="Enter Your Tiemzone (ex: EST, PST, etc.)",
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.add_item(self.codename)
        self.add_item(self.roblox_name)
        self.add_item(self.timezone)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user.id
        guild = interaction.guild.id
        r_name = self.roblox_name.value
        timezone = self.timezone.value
        codename = self.codename.value

        profile = {
                'user_id': user,
                'guild_id': guild,
                'codename': codename,
                'roblox_name': r_name,
                'unit': {},
                'private_unit': [],
                'status': 'Active',
                'join_date': str(datetime.now().date()),
                'timezone': timezone,
            }

        await profiles.insert_one(profile)

        embed = discord.Embed(
                                title="Profile Created!",
                                description=f"Your profile has been created!\n\n**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Current Points: **0\n**Total Points: **0",
                                color=discord.Color.green()
                                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        dm_embed = profile_creation_embed()
        await interaction.user.send(embed=dm_embed)