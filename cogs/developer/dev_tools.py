import discord
from discord.ext import commands
from utils.constants import profiles
from utils.utils import fetch_unit_options


class DevTools(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


    @commands.command(name="manage_profile")
    @commands.is_owner()
    async def dev_manage_profile(self, ctx: commands.Context, user: discord.Member):
        return

async def setup(bot: commands.Bot):
    await bot.add_cog(DevTools(bot=bot))