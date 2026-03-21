import discord
from discord.ext import commands
from utils.constants import loa, MESSAGE_CODE_RE, active_sessions
from utils.utils import tts_to_file, tts_match_object, tts_logic, fetch_id
import os
import asyncio
import time

class Messaging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_speaker = {}
        self.last_message_time = {}

    def _create_after_playback(self, file, queue):
        def _after_playback(error):
            if error:
                print(f"Playback error: {error}")

            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                print(f"Cleanup failed: {e}")

            self.bot.loop.call_soon_threadsafe(queue.task_done)

        return _after_playback

    async def _play_audio(self, vc: discord.VoiceClient, source, file, queue):
        try:
            vc.play(source, after=self._create_after_playback(file, queue))
        except Exception as e:
            print(f"vc.play failed: {e}")
            try:
                if os.path.exists(file):
                    os.remove(file)
            finally:
                queue.task_done()
            return

        while vc.is_connected() and vc.is_playing():
            await asyncio.sleep(0.1)
    
    async def tts_player(self, guild: discord.Guild):
        queue: asyncio.Queue = self.bot.tts_queues[guild.id]

        try:
            while True:
                file = await queue.get()
                vc: discord.VoiceClient = guild.voice_client

                source = tts_logic(queue, vc, file)
                if not source:
                    continue

                await self._play_audio(vc, source, file, queue)

        except asyncio.CancelledError:
            # allows clean shutdowns
            raise
        except Exception as e:
            print(f"TTS player crashed in guild {guild.id}: {e}")
    
    async def LOA_Event(self, message: discord.Message):
        if message.mentions != []:
            for mention in message.mentions:
                result = await loa.find_one({"guild_id": message.guild.id, "user_id": mention.id})
                if result:
                    embed = discord.Embed(title="On LOA", description=f"Please refrain from pinging **{mention.name}**", color=discord.Color.dark_embed())
                    await message.reply(embed=embed)
                else:
                    return
    
    async def Auto_Reply_Event(self, message: discord.Message):
        try:
            for auto_reply in self.bot.auto_replys:
                if auto_reply['guild_id'] == message.guild.id and auto_reply['message'] == message.content:
                    await message.channel.send(auto_reply['response'])
        except AttributeError:
            pass
    
    async def TTS_Event(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.voice: 
            if message.content.startswith("-"):
                return
            
            bot_vc = message.guild.voice_client 
            guild_id = message.guild.id
            user = message.author
            now = time.time()
            if bot_vc and message.channel == message.guild.voice_client.channel: 
                content = tts_match_object(message)

                last_speaker = self.last_speaker.get(guild_id)
                last_message_time = now - self.last_message_time.get(guild_id, 0)

                file = await tts_to_file(user, last_speaker, last_message_time, str(content)) 

                self.last_speaker[guild_id] = message.author.id
                self.last_message_time[guild_id] = now
                
                queue = self.bot.tts_queues[message.guild.id]
                await queue.put(file)

                if message.guild.id not in self.bot.tts_tasks or self.bot.tts_tasks[message.guild.id].done():
                    self.bot.tts_tasks[message.guild.id] = self.bot.loop.create_task(
                        self.tts_player(message.guild)
                    )
    
    async def React_To_Message(self, message: discord.Message):
        try:
            results = await fetch_id(message.guild.id, ["sessions_channel_id", "event_channel_id", "mission_channel_id", "training_channel_id"])

            valid_channels = [results["sessions_channel_id"], results["event_channel_id"], results["mission_channel_id"], results["training_channel_id"]]
            if message.channel.id in valid_channels and MESSAGE_CODE_RE.search(message.content):
                await message.add_reaction("🟩")
                await message.add_reaction("🟨")
                await message.add_reaction("🟥")

                await active_sessions.update_one(
                {"guild_id": message.guild.id},
                {
                    "$set": {
                        f"active_votes.{message.channel.id}": message.id
                    }
                },
                upsert=True
            )
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        
        if message.author == self.bot.user:
            return
        
        # Checking for LOA Pings
        await self.LOA_Event(message)

        # Auto Reply System
        await self.Auto_Reply_Event(message)

        # Text to Speech
        await self.TTS_Event(message)

        # Session Votes
        await self.React_To_Message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(Messaging(bot))