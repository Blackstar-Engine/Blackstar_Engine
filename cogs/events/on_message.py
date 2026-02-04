import discord
from discord.ext import commands
from utils.constants import loa
from utils.utils import tts_to_file
import os
class AutoReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        
        if message.author == self.bot.user:
            return
        
        # Checking for LOA Pings
        if message.mentions != []:
            for mention in message.mentions:
                result = await loa.find_one({"guild_id": message.guild.id, "user_id": mention.id})
                if result:
                    embed = discord.Embed(title="On LOA", description=f"Please refrain from pinging **{mention.name}**", color=discord.Color.dark_embed())
                    await message.reply(embed=embed)
                else:
                    return

        # Auto Reply System
        for auto_reply in self.bot.auto_replys:
            if auto_reply['guild_id'] == message.guild.id and auto_reply['message'] == message.content:
                await message.channel.send(auto_reply['response'])
        
        # Emoji added by role

        # Text to Speech
        if message.channel.type == discord.ChannelType.voice:
            file = tts_to_file(message.author.display_name, str(message.content))
            source = discord.FFmpegPCMAudio(file)

            try:
                message.guild.voice_client.play(source, after = lambda e: os.remove(file))
            except AttributeError:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReply(bot))