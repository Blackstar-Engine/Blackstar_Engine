import discord
from discord.ext import commands
from datetime import timedelta

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="execute", description="Execute the user")
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        # foundation command
        print("hit")
        duration = timedelta(seconds=10)
        try:
            await user.timeout(duration=duration, reason="Funny Command")
        except Exception:
            return await ctx.send("Something has gone wrong with timeing out the user!")

        await ctx.send(f"{user.mention} hass been executed by the order of {ctx.author.mention}!")

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))