import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime
from utils.utils import permissions
from utils.constants import economy_profiles
class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        self.bot.tree.clear_commands(guild=ctx.guild)
        await ctx.send("cleared all commands")
        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.send("synced commands")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))