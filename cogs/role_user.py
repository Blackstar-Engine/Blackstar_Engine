import discord
from discord.ext import commands
from utils.utils import role_user, has_approval_perms

class RoleUser(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="roleuser", description="Auto give a user the overall and first rank role of a unit", with_app_command=True)
    async def role_user(self, ctx: commands.Context, user: discord.Member, unit: str):
        if not await has_approval_perms(ctx, 2):
            return
        
        result = await role_user(ctx, unit)
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