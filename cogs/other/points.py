import discord
from discord.ext import commands
from utils.utils import interaction_check
from utils.constants import profiles

class AcceptDenyButtons(discord.ui.View):
    def __init__(self, bot, points, embed, profile):
        super().__init__(timeout=None)
        self.bot = bot
        self.points = points
        self.embed: discord.Embed = embed
        self.profile = profile
    
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="points_accept_button")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        '''
        if self.points >= 1 and self.points <= 1.5:
            ia can accept
        elif self.points >= 1.5 and self.points <= 2:
            central command
            high command
        elif self.points >= 2 and self.points <= 7.99:
            site command
        elif self.points >= 8:
            foundation command
            wolf (user)
        '''

        await profiles.update_one(self.profile, {'$inc': {"current_points": self.points}})
        
        self.embed.color = discord.Color.green()
        self.embed.title = "Points Accepted"

        await self.user.send(f"Your points request for **{self.points}** in **{interaction.guild.name}** has been **ACCEPTED**!")
        await interaction.response.edit_message(content=None, view=None, embed=self.embed)

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
        pass

    @points.command(name="request", description="Request points to be added to your profile")
    async def request(self, ctx: commands.Context, points: float):
        if points <= 0 or not isinstance(points, float):
            await ctx.send("Please make sure the number is positive and is an number.", ephemeral=True)
        
        embed=discord.Embed(title="Points Requested", 
                            description=f"**{points}** point(s) have been successfully requested!",
                            color=discord.Color.green())
        
        profile = await profiles.find_one({"guild_id": ctx.guild.id, "user_id": ctx.author.id})

        mod_embed = discord.Embed(title="New Points Request",
                                  description=f"**User: ** {ctx.author.mention}(`{ctx.author.id}`)\n**Points: ** {points}",
                                  color=discord.Color.yellow())
        mod_embed.add_field(name="__Profile Info:__",
                            value=f"**Codename: ** {profile.get('codename')}\n**Rank: ** {profile.get('rank')}\n**Join Date: ** {profile.get('join_date')}\n**Current Points: ** {profile.get('current_points')}\n**Total Points: ** {profile.get('total_points')}")


        view = AcceptDenyButtons(self.bot, points, mod_embed, profile)

        channel = await self.bot.fetch_channel(1453154400989085738)
        await channel.send(embed=mod_embed, view=view)

        await ctx.send(embed=embed)
    # 2
    # 3 - 4
    # 5+

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))