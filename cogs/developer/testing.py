import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime
from utils.utils import has_approval_perms

class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    # @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        await has_approval_perms(ctx.author, 3)

        await ctx.send("hit")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))