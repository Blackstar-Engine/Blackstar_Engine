import discord
from discord.ext import commands

from datetime import datetime

from utils.constants import birthdays

class Birthday(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_group(invoke_without_sub_command=False)
    async def birthday(self, ctx: commands.Context):
        return
    
    @birthday.command(name="set", description="Set your birthday", with_app_command=True)
    async def set(self, ctx: commands.Context, date):
        try:
            birthday = datetime.strptime(date, "%m/%d")
            string = birthday.strftime("%m-%d")
            display = birthday.strftime("%B %d").replace(" 0", " ")

            await birthdays.update_one({"user_id": ctx.author.id}, {"$set": {"date": string}}, upsert=True)
            embed = discord.Embed(description=f"Your birthday has been set to `{display}`", color=discord.Color.light_gray())
            await ctx.send(embed=embed, ephemeral=True)
        except ValueError:
            embed = discord.Embed(description="Please use MM/DD format.", color=discord.Color.light_gray())
            await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot=bot))