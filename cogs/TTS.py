import discord 
from discord.ext import commands
import os
import asyncio

class tts_system_commands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    @commands.hybrid_command(name="join", description="Have the bot join your current VC.")
    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        if not ctx.author.voice:
            embed = discord.Embed(title="Whoops....", description="Please make sure you are in a channel!", color=discord.Color.light_grey())
            return await ctx.send(embed=embed, ephemeral=True)
        
        if not channel:
            channel = ctx.author.voice.channel
        
        if ctx.voice_client is None:
            await channel.connect(self_deaf=True)
        else:
            await ctx.guild.voice_client.disconnect()
            await channel.connect(self_deaf=True)

        embed = discord.Embed(title="Connected!", description=f"Connected to {channel.mention}!", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    @commands.hybrid_command(name="leave", description="Have the bot leave your current VC.")
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client is not None:
            channel: discord.VoiceChannel = ctx.voice_client.channel

            await ctx.guild.voice_client.disconnect()
            self.bot.tts_queues.clear()

            try:
                
                for entry in os.scandir("."):
                    if entry.is_file() and entry.name.startswith("tts_") and entry.name.endswith(".mp3"):
                        try:
                            os.remove(entry.path)
                        except OSError:
                            pass
            except Exception as e:
                print("Failed to remove TTS files: ", e)
            
            embed = discord.Embed(title="Disconnected!", description=f"Disconnected from {channel.mention}!", color=discord.Color.green())
            embed.set_footer(text=f"Executed by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Whoops....", description="I need be in a channel to leave!", color=discord.Color.light_grey())
            await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="clear", description="Clear the TTS queue.")
    async def clear(self, ctx: commands.Context):
        guild_id = ctx.guild.id

        # 1. Stop voice playback
        vc = ctx.guild.voice_client
        queue = self.bot.tts_queues[guild_id]

        if vc and vc.is_playing():
            vc.stop()
        elif vc is None or queue.empty():
            return await ctx.send("There is nothing to clear!", ephemeral=True)

        # 2. Drain the queue
        

        while not queue.empty():
            try:
                file = queue.get_nowait()
                queue.task_done()

                # delete queued file immediately
                if os.path.exists(file):
                    os.remove(file)

            except asyncio.QueueEmpty:
                break

        # 3. Cancel TTS worker
        task = self.bot.tts_tasks.get(guild_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            finally:
                del self.bot.tts_tasks[guild_id]

        # 4. Delete stray mp3 files
        for entry in os.scandir("."):
            if entry.is_file() and entry.name.startswith("tts_") and entry.name.endswith(".mp3"):
                try:
                    os.remove(entry.path)
                except OSError:
                    pass

        embed = discord.Embed(title="Queue Cleared!", description="All records have been cleared", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(tts_system_commands(bot))