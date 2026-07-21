import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime
from utils.utils import has_approval_perms, permissions
from utils.constants import economy_profiles
class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    @permissions()
    async def testing(self, ctx: commands.Context):
        await ctx.send("You have access")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))