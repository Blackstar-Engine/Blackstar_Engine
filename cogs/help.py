import discord
from discord.ext import commands
from datetime import datetime

from ui.help.Pages import Pages

class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Get help with commands")
    async def help(self, ctx: commands.Context):
        view = Pages()
        await ctx.send(embed=view.embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))