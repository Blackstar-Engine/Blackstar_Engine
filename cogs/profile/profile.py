import discord
from discord.ext import commands
from utils.constants import profiles
from datetime import datetime

class CreateProfileModal(discord.ui.Modal):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(title="Create Your Profile")

        self.codename = discord.ui.TextInput(
            label="Codename",
            placeholder="Create a codename for yourself",
            required=True,
            max_length=5,
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
                'unit': [],
                'private_unit': [],
                'rank': 'Recruit',
                'current_points': 0,
                'total_points': 0,
                'status': 'Active',
                'join_date': str(datetime.now().date()),
                'timezone': timezone,
                'trainings': [],
                'missions': []
            }

        await profiles.insert_one(profile)

        embed = discord.Embed(
                                title="Profile Created!",
                                description=f"Your profile has been created!\n\n**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Current Points: **0\n**Total Points: **0",
                                color=discord.Color.green()
                                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

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

        

class CTXCreateProfileButton(discord.ui.View):
    def __init__(self, bot, user: discord.User):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="Create Profile", style=discord.ButtonStyle.green, custom_id="create_profile_button")
    async def create_profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Sorry but you can't use this button.", ephemeral=True)

        modal = CreateProfileModal(self.bot)
        await interaction.response.send_modal(modal)

class ProfileButtons(discord.ui.View):
    def __init__(self, bot, user: discord.User, profile: dict, embed: discord.Embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.profile = profile
        self.embed = embed
    
    @discord.ui.button(label="Edit Profile", style=discord.ButtonStyle.grey)
    async def edit_profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("Sorry but you can't use this button.", ephemeral=True)

        modal = EditProfileModal(self.bot, self.profile, self.embed)
        await interaction.response.send_modal(modal)
    


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="View or create your profile in the server.", with_app_command=True)
    async def profile(self, ctx: commands.Context):
        profile = await profiles.find_one({'user_id': ctx.author.id, 'guild_id': ctx.guild.id})
        if not profile:
            try:
                modal = CreateProfileModal(self.bot)
                await ctx.interaction.response.send_modal(modal)
            except AttributeError:
                view = CTXCreateProfileButton(self.bot, ctx.author)
                await ctx.send("Please click the button to continue!", view=view)
        else:
            unit = ", ".join(profile.get('unit', []))
            private_unit = ", ".join(profile.get('private_unit', []))
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Rank: ** {profile.get('rank')}\n**Unit(s): **{unit}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="Points", value=f"**Current Points: **{profile.get('current_points')}\n**Total Points: **{profile.get('total_points')}", inline=True)
            embed.add_field(name="Trainings Completed", value=f"{len(profile.get('tainings', []))} training(s) completed.", inline=True)
            embed.add_field(name="Missions Completed", value=f"{len(profile.get('missions', []))} mission(s) completed.", inline=True)

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            view = ProfileButtons(self.bot, ctx.author, profile, embed)

            await ctx.send(embed=embed, view=view)



async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))

# points, sessions (trainings and missions)