import discord
from discord.ext import commands

from datetime import datetime

from utils.constants import birthdays

class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_group(name="birthday")
    async def birthday(self, ctx: commands.Context):
        return
    
    @birthday.command(name="set", description="Set your birthday")
    async def set(self, ctx: commands.Context, date):
        info = await birthdays.find_one({"user_id":ctx.author.id})
        if info:
            embed = discord.Embed(description="Your birthday has already been set, please contact DSM to change it.", color=discord.Color.light_gray())
            return await ctx.send(embed=embed, ephemeral=True)
        try:
            birthday = datetime.strptime(date, "%m/%d")
            string = birthday.strftime("%m-%d")
            display = birthday.strftime("%B %d").replace(" 0", " ")

            birthdays.insert_one({"user_id": ctx.author.id, "date": string})
            embed = discord.Embed(description=f"Your birthday has been set to `{display}`", color=discord.Color.light_gray())
            await ctx.send(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(description="Please use MM/DD format.", color=discord.Color.light_gray())
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot=bot))