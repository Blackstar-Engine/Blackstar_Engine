import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime

class testingvc(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(placeholder="select something", channel_types=[discord.ChannelType.voice], min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        return

class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        channel = testingvc()
        view = discord.ui.View()

        view.add_item(channel)

        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))