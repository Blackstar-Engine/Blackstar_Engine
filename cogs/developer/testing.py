import discord
from discord.ext import commands

class DevTestingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        raise commands.CommandError("testing")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))