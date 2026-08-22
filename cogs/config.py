import discord
from discord.ext import commands
from utils.utils import permissions

class ConfigCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="config", description="Configure modulas within the bot such as LOA and Sessions", with_app_command=True, extras={'category': 'Administration'})
    @permissions()
    async def config(self, ctx: commands.Context):
        return

async def setup(bot: commands.Bot):
    await bot.add_cog(ConfigCommand(bot))