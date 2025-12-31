import discord
from discord.ext import commands
from utils.constants import profiles, foundation_command, site_command, high_command, central_command, ia_id, wolf_id

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

        mod_embed = discord.Embed(title="New Points Request",
                                  description=f"**User: ** {ctx.author.mention}\n** Requested Points: ** {points}\n**Proof: ** {channel}",
                                  color=discord.Color.light_grey())
        
        mod_embed.add_field(name="__Profile Info:__",
                            value=f"> **Codename: ** {profile.get('codename')}\n> **Rank: ** {profile.get('rank')}\n> **Join Date: ** {profile.get('join_date')}\n> **Current Points: ** {profile.get('current_points')}\n> **Total Points: ** {profile.get('total_points')}")


        view = AcceptDenyButtons(self.bot, ctx.author, points, mod_embed, profile)

        channel = await self.bot.fetch_channel(1453154400989085738)
        await channel.send(embed=mod_embed, view=view)

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))