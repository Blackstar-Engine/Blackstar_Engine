import discord
from discord.ext import commands

class AutoReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        for auto_reply in self.bot.auto_replys:
            if auto_reply['guild_id'] == message.guild.id and auto_reply['message'] == message.content:
                await message.channel.send(auto_reply['response'])

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReply(bot))