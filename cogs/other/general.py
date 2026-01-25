import discord
from discord.ext import commands
from datetime import timedelta
from utils.constants import foundation_command

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="execute", description="Execute the user")
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        foundation_role = await ctx.guild.fetch_role(foundation_command)

        if foundation_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of foundation to use this command!", ephemeral=True)

        duration = timedelta(seconds=10)
        try:
            await user.timeout(duration, reason="Execute Command")
        except Exception as e:
            raise commands.CommandInvokeError(e) from e

        await ctx.send(f"{user.mention} has been executed by the order of {ctx.author.mention}!")

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))