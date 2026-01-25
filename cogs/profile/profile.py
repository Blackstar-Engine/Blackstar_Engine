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
                'current_points': 0,
                'total_points': 0,
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

        dm_embed=discord.Embed(
            title="Welcome to Blackstar!",
            description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            color=discord.Color.light_grey()
        )
        await interaction.user.send(embed=dm_embed)

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

class UnitSelectView(discord.ui.View):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

        self.dept_role_select.options = options
    
    @discord.ui.select(
        placeholder="Select a Role",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def dept_role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        value = select.values[0]

        select.values.clear()

        await interaction.edit_original_response(view=self)

        if value == "no_units":
            return
        
        department = self.profile["unit"][value]

        embed = discord.Embed(
            title="Unit Information",
            description=f"**Unit Name: ** {value}\n**Rank: ** {department.get('rank')}",
            color=discord.Color.light_grey()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

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
            options = []
            units = dict(profile.get("unit", {}))

            for unit, data in units.items():
                if data.get("is_active"):
                    options.append(discord.SelectOption(label=unit))
            
            if options == []:
                options.append(discord.SelectOption(label="No Active Units", value="no_units"))

            private_unit = ", ".join(profile.get('private_unit', []))
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="Points", value=f"**Current Points: **{profile.get('current_points')}\n**Total Points: **{profile.get('total_points')}", inline=True)

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            view = UnitSelectView(self.bot, options, profile)

            await ctx.send(embed=embed, view=view, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))