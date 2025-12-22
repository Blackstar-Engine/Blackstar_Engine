import discord
from discord.ext import commands

class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 2
    # 3 - 4
    # 5+

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))