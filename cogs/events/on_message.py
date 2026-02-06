import discord
from discord.ext import commands
from utils.constants import loa, TTSEmojiRegFormat
from utils.utils import tts_to_file
import os
import asyncio
from collections import defaultdict
import re

class AutoReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def tts_player(self, guild: discord.Guild):
        vc = guild.voice_client
        queue = self.bot.tts_queues[guild.id]

        try:
            while True:
                file = await queue.get()

                # File was deleted by clear() — skip it
                if not os.path.exists(file):
                    queue.task_done()
                    continue

                if not vc or not vc.is_connected():
                    if os.path.exists(file):
                        os.remove(file)
                    queue.task_done()
                    break

                try:
                    source = discord.FFmpegPCMAudio(file)
                except Exception:
                    # FFmpeg couldn't open it — just skip
                    if os.path.exists(file):
                        os.remove(file)
                    queue.task_done()
                    continue

                vc.play(
                    source,
                    after=lambda e: (
                        os.path.exists(file) and os.remove(file),
                        self.bot.loop.call_soon_threadsafe(queue.task_done)
                    )
                )

                while vc.is_playing():
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            return

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
            bot_vc = message.guild.voice_client 
            if bot_vc and message.channel == message.guild.voice_client.channel: 
                match = re.sub(TTSEmojiRegFormat, "emoji", message.content)
                if match:
                    message.content = match
                if message.content.startswith("https://"):
                    message.content = "an image"
                elif message.content.startswith("<@"):
                    message.content = "pinged someone"
                elif message.content.startswith("<#"):
                    message.content = "sent a channel"

                file = tts_to_file(message.author.display_name, str(message.content)) 
                queue = self.bot.tts_queues[message.guild.id]
                await queue.put(file)

                if message.guild.id not in self.bot.tts_tasks or self.bot.tts_tasks[message.guild.id].done():
                    self.bot.tts_tasks[message.guild.id] = self.bot.loop.create_task(
                        self.tts_player(message.guild)
                    )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoReply(bot))