import discord
from discord.ext import commands
from utils.constants import whitelisted_guilds

class OnGuildJoin(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in whitelisted_guilds:
            try:
                await guild.owner.send("I am a whitelisted only bot, you are not allowed to invite me!")
                await guild.leave()
            except Exception:
                await guild.owner.send(f"Please remove me from **{guild.name}**, I will not work!")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnGuildJoin(bot=bot))