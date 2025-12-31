import discord
from discord.ext import commands
from utils.constants import profiles, foundation_command, site_command, high_command, central_command, ia_id, wolf_id, departments

class AcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, user, points, embed, profile):
        super().__init__(timeout=None)
        self.bot = bot
        self.points = points
        self.embed: discord.Embed = embed
        self.profile = profile
        self.user: discord.Member = user

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
                "current_points": self.points,
                "total_points": self.points
            }}
        )

        self.embed.color = discord.Color.green()
        self.embed.title = "Points Accepted"

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
        
        await self.user.send(f"Your points request for **{self.points}** in **{interaction.guild.name}** has been **DENIED**!")
        await interaction.response.edit_message(content=None, view=None, embed=self.embed)

class UnitSelectView(discord.ui.View):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

        self.dept = None

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

        if value == "no_units":
            self.dept = "no_unit"
        else:
            self.dept = value

        self.stop()

class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="points")
    async def points(self, ctx: commands.Context):
        return

    @points.command(name="request", description="Request points to be added to your profile")
    async def request(self, ctx: commands.Context, points: float, channel):
        if points <= 0 or not isinstance(points, float):
            await ctx.send("Please make sure the number is positive and is an number.", ephemeral=True)
        
        embed=discord.Embed(title="Points Requested", 
                            description=f"**{points}** point(s) have been successfully requested!",
                            color=discord.Color.green())
        
        profile = await profiles.find_one({"guild_id": ctx.guild.id, "user_id": ctx.author.id})

        options = []
        units = profile.get("unit")

        for unit, data in units.items():
            if data.get("is_active"):
                options.append(discord.SelectOption(label=unit))
        
        if options == []:
            options.append(discord.SelectOption(label="No Active Units", value="no_units"))

        unit_select_view = UnitSelectView(self.bot, options, profile)
        unit_select_embed = discord.Embed(title="Select a Unit", description="Please select a unit you would like this point request to send to!", color=discord.Color.light_grey())

        await ctx.send(embed=unit_select_embed, view=unit_select_view)

        await unit_select_view.wait()

        dept = unit_select_view.dept

        channel_id = await departments.find_one({"display_name": dept})

        channel_var = ctx.guild.get_channel(int(channel_id.get("points_request_channel")))

        mod_embed = discord.Embed(title="New Points Request",
                                  description=f"**User: ** {ctx.author.mention}\n** Requested Points: ** {points}\n**Proof: ** {channel}",
                                  color=discord.Color.light_grey())
        
        mod_embed.add_field(name="__Profile Info:__",
                            value=f"> **Codename: ** {profile.get('codename')}\n> **Rank: ** {profile.get('rank')}\n> **Join Date: ** {profile.get('join_date')}\n> **Current Points: ** {profile.get('current_points')}\n> **Total Points: ** {profile.get('total_points')}")


        accept_deny_buttons_view = AcceptDenyButtons(self.bot, ctx.author, points, mod_embed, profile)

        await channel_var.send(embed=mod_embed, view=accept_deny_buttons_view)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))