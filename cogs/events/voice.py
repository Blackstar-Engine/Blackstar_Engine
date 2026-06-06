import discord
from discord.ext import commands
import asyncio
from cogs.TTS import tts_system_commands
from utils.constants import active_sessions
from datetime import datetime, UTC

class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
    
    async def clear_queue(self, queue, guild_id):
        try:
            tts_system_commands._drain_queue(self, queue)
            await tts_system_commands._cancel_tts_task(self, guild_id)
            tts_system_commands._cleanup_mp3_files(self)
        except Exception as e:
            print(f"VC Update Error: {e}")
    
    async def handle_tts_logic(self, vc: discord.VoiceClient, member: discord.Member, before: discord.VoiceState):
        channel = vc.channel
        guild_id = member.guild.id
        queue = self.bot.tts_queues[guild_id]

        if before.channel == channel:
            humans = [m for m in channel.members if not m.bot]

            if len(humans) == 0:
                await asyncio.sleep(30)

                current_vc = member.guild.voice_client
                if not current_vc or current_vc.channel != channel:
                    return

                humans_after = [m for m in current_vc.channel.members if not m.bot]
                if len(humans_after) == 0:
                    await current_vc.disconnect()
                    await self.clear_queue(queue, guild_id)
                    
                else:
                    # There are now people in the same channel, so keep the bot connected
                    return
    
    async def handle_session_logic(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # if active session in the vc
        # if user joins vc, add to the attendees list and set join datetime
        # if user leaves vc, close the current period and append it to the timeline

        guild_id = member.guild.id
        user_key = str(member.id)
        now = datetime.now(UTC)

        left_channel = before.channel
        joined_channel = after.channel

        # USER LEFT VC
        if left_channel:

            session = await active_sessions.find_one({
                "guild_id": guild_id,
                "vc_channel_id": left_channel.id,
                "status": "active"
            })

            if session:

                attendance = session.get("attendance", {})
                record = attendance.get(user_key)

                if record and record.get("currently_in"):

                    join_time = record.get("joined_at") or session.get("started_at") or now
                    if join_time.tzinfo is None:
                        join_time = join_time.replace(tzinfo=UTC)

                    left_time = now
                    duration = (left_time - join_time).total_seconds()
                    if duration < 0:
                        duration = 0

                    total_seconds = record.get("total_seconds", 0) + duration
                    period = {
                        "joined_at": join_time,
                        "left_at": left_time,
                        "duration": duration
                    }

                    await active_sessions.update_one(
                        {"_id": session["_id"]},
                        {
                            "$push": {
                                f"attendance.{user_key}.periods": period
                            },
                            "$set": {
                                f"attendance.{user_key}.left_at": left_time,
                                f"attendance.{user_key}.last_left_at": left_time,
                                f"attendance.{user_key}.currently_in": False,
                                f"attendance.{user_key}.total_seconds": total_seconds
                            }
                        }
                    )

        # USER JOINED VC
        if joined_channel:

            session = await active_sessions.find_one({
                "guild_id": guild_id,
                "vc_channel_id": joined_channel.id,
                "status": "active"
            })

            if session:

                attendance = session.get("attendance", {})
                existing = attendance.get(user_key)

                if existing and existing.get("currently_in"):
                    return

                join_time = now
                update_doc = {
                    f"attendance.{user_key}.joined_at": join_time,
                    f"attendance.{user_key}.left_at": None,
                    f"attendance.{user_key}.currently_in": True
                }

                if existing:
                    if existing.get("first_joined_at") is None:
                        update_doc[f"attendance.{user_key}.first_joined_at"] = join_time
                    if existing.get("periods") is None:
                        update_doc[f"attendance.{user_key}.periods"] = []
                    if existing.get("total_seconds") is None:
                        update_doc[f"attendance.{user_key}.total_seconds"] = 0
                else:
                    update_doc.update({
                        f"attendance.{user_key}.first_joined_at": join_time,
                        f"attendance.{user_key}.total_seconds": 0,
                        f"attendance.{user_key}.periods": []
                    })

                await active_sessions.update_one(
                    {"_id": session["_id"]},
                    {"$set": update_doc}
                )


        

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        await self.bot.wait_until_ready()

        vc = member.guild.voice_client
        if vc:
            await self.handle_tts_logic(vc, member, before)

        await self.handle_session_logic(member, before, after)
        
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot=bot))
