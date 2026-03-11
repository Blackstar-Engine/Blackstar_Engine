import discord
from discord.ext import commands
import asyncio
from cogs.TTS import tts_system_commands

class OnVCStateUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        await self.bot.wait_until_ready()

        vc = member.guild.voice_client

        if not vc:
            return
        
        channel = vc.channel
        guild_id = member.guild.id
        queue = self.bot.tts_queues[guild_id]

        if before.channel == channel:
            humans = [m for m in channel.members if not m.bot]

            if len(humans) == 0 or not humans:
                await asyncio.sleep(30)
                await vc.disconnect()

                try:
                    tts_system_commands._drain_queue(self, queue)
                    await tts_system_commands._cancel_tts_task(self, guild_id)
                    tts_system_commands._cleanup_mp3_files(self)
                except Exception as e:
                    print(f"VC Update Error: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnVCStateUpdate(bot=bot))
