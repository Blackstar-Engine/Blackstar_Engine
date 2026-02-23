import discord
from discord.ext import commands
from utils.constants import departments, mtf_overall_role_id, central_command, high_command, site_command, foundation_command, drm_id
from utils.utils import fetch_department

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
        
        unit = unit.upper()

        department = await fetch_department(ctx, unit)

        if not department:
            embed = discord.Embed(title="No Department Found", description=f"I couldd not find a department with the name `{unit}`", color=discord.Color.red())
            return await ctx.send(embed=embed, ephemeral=True)

        overall_role_id = department.get('role_id')
        first_rank_role_id = department.get('first_rank_id')

        if unit.startswith("MTF"):
            mtf_overall_role_obj = ctx.guild.get_role(mtf_overall_role_id)

        overall_role_obj = ctx.guild.get_role(overall_role_id)
        first_rank_role_obj = ctx.guild.get_role(first_rank_role_id)

        if not overall_role_obj or not first_rank_role_obj:
            embed = discord.Embed(title="Role Not Found", description=f"I could not find the overall or first rank role for the `{unit}` department. Please make sure they are setup correctly.", color=discord.Color.red())
            return await ctx.send(embed=embed, ephemeral=True)
        elif overall_role_obj in user.roles and first_rank_role_obj in user.roles:
            embed = discord.Embed(title="User Already Has Roles", description=f"{user.mention} is already in `{unit}`.", color=discord.Color.yellow())
            return await ctx.send(embed=embed, ephemeral=True)
        
        try:
            if unit.startswith("MTF"):
                await user.add_roles(mtf_overall_role_obj, overall_role_obj, first_rank_role_obj, reason=f"Role User Command used by {ctx.author}")
            else:
                await user.add_roles(overall_role_obj, first_rank_role_obj, reason=f"Role User Command used by {ctx.author}")

            embed = discord.Embed(title="Roles Added", description=f"Successfully added the overall and first rank role for the `{unit}` department to {user.mention}", color=discord.Color.green())
            await ctx.send(embed=embed, ephemeral=True)

            await user.send(f"You were added to `{unit}` in **{ctx.guild.name}**. If this is a mistake, please open a ticket!")
        except discord.Forbidden:
            embed = discord.Embed(title="Permission Error", description=f"I do not have permission to add roles to {user.mention}. Please make sure my role is higher than the overall and first rank role for the `{unit}` department.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleUser(bot))