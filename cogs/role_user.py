import discord
from discord.ext import commands
from utils.constants import central_command, high_command, site_command, foundation_command, drm_id
from utils.utils import role_user

class RoleUser(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="roleuser", description="Auto give a user the overall and first rank role of a unit", with_app_command=True)
    async def role_user(self, ctx: commands.Context, user: discord.Member, unit: str):
        central_role = ctx.guild.get_role(central_command)
        high_role = ctx.guild.get_role(high_command)
        site_role = ctx.guild.get_role(site_command)
        foundation_role = ctx.guild.get_role(foundation_command)
        drm_role = ctx.guild.get_role(drm_id)

        if not any(role in ctx.author.roles for role in [central_role, high_role, site_role, foundation_role, drm_role]):
            embed = discord.Embed(title="Permission Denied", description="You need to be apart of either foundation, site, central, high command, or the DRM to use this command.", color=discord.Color.red())
            return await ctx.send(embed=embed, ephemeral=True)
        
        result = await self.role_user(ctx, unit)
        if not result:
            return
        
        try:
            embed = discord.Embed(title="Roles Added", description=f"Successfully added the overall and first rank role for the `{unit}` department to {user.mention}", color=discord.Color.green())
            await ctx.send(embed=embed, ephemeral=True)

            await user.send(f"You were added to `{unit}` in **{ctx.guild.name}**. If this is a mistake, please open a ticket!")
        except discord.Forbidden:
            embed = discord.Embed(title="Permission Error", description=f"I do not have permission to add roles to {user.mention}. Please make sure my role is higher than the overall and first rank role for the `{unit}` department.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleUser(bot))