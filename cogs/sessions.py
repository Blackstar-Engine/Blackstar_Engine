import discord
from discord.ext import commands
from utils.constants import MESSAGE_CODE_RE, active_sessions
from utils.utils import has_approval_perms, fetch_id
from ui.sessions.views.VCChannelSelect import VCChannelSelectView
from datetime import datetime, UTC


class Sessions(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def _fallback_first_joined(self, info, session):
        joined_at = info.get("first_joined_at") or info.get("joined_at") or session.get("started_at")
        if joined_at and joined_at.tzinfo is None:
            joined_at = joined_at.replace(tzinfo=UTC)
        return joined_at

    def _fallback_last_left(self, info, session, session_end=None):
        left_at = info.get("last_left_at") or info.get("left_at") or session_end or session.get("ended_at")
        if left_at and left_at.tzinfo is None:
            left_at = left_at.replace(tzinfo=UTC)
        return left_at

    async def _cleanup_user(self, session, session_end):
        for user_id, info in session.get("attendance", {}).items():
            currently_in = info.get("currently_in", False)
            first_joined_at = self._fallback_first_joined(info, session)
            last_left_at = self._fallback_last_left(info, session, session_end)
            total_seconds = info.get("total_seconds", 0)
            periods = info.get("periods") or []

            if currently_in:
                join_time = info.get("joined_at") or session.get("started_at") or session_end
                if join_time and join_time.tzinfo is None:
                    join_time = join_time.replace(tzinfo=UTC)

                left_time = session_end
                duration = (left_time - join_time).total_seconds()
                if duration < 0:
                    duration = 0

                total_seconds += duration
                period = {
                    "joined_at": join_time,
                    "left_at": left_time,
                    "duration": duration
                }

                await active_sessions.update_one(
                    {"_id": session["_id"]},
                    {
                        "$push": {f"attendance.{user_id}.periods": period},
                        "$set": {
                            f"attendance.{user_id}.currently_in": False,
                            f"attendance.{user_id}.first_joined_at": first_joined_at,
                            f"attendance.{user_id}.last_left_at": left_time,
                            f"attendance.{user_id}.left_at": left_time,
                            f"attendance.{user_id}.total_seconds": total_seconds
                        }
                    }
                )
                continue

            if not periods and info.get("joined_at") and info.get("left_at"):
                joined_at = info.get("joined_at")
                left_at = info.get("left_at")
                if joined_at and joined_at.tzinfo is None:
                    joined_at = joined_at.replace(tzinfo=UTC)
                if left_at and left_at.tzinfo is None:
                    left_at = left_at.replace(tzinfo=UTC)

                duration = (left_at - joined_at).total_seconds()
                if duration < 0:
                    duration = 0

                total_seconds = max(total_seconds, duration)
                period = {
                    "joined_at": joined_at,
                    "left_at": left_at,
                    "duration": duration
                }

                await active_sessions.update_one(
                    {"_id": session["_id"]},
                    {
                        "$push": {f"attendance.{user_id}.periods": period},
                        "$set": {
                            f"attendance.{user_id}.first_joined_at": first_joined_at,
                            f"attendance.{user_id}.last_left_at": last_left_at,
                            f"attendance.{user_id}.left_at": left_at,
                            f"attendance.{user_id}.total_seconds": total_seconds
                        }
                    }
                )
                continue

            await active_sessions.update_one(
                {"_id": session["_id"]},
                {
                    "$set": {
                        f"attendance.{user_id}.first_joined_at": first_joined_at,
                        f"attendance.{user_id}.last_left_at": last_left_at,
                        f"attendance.{user_id}.currently_in": False,
                        f"attendance.{user_id}.left_at": last_left_at,
                        f"attendance.{user_id}.total_seconds": total_seconds,
                        f"attendance.{user_id}.periods": periods
                    }
                }
            )

    @commands.hybrid_group(name="session")
    async def session(self, ctx: commands.Context):
        # parent command
        pass

    @session.command(name="start", description="Start a new session in this channel (Central Command+).", extras={'category': 'Sessions'})
    async def session_start(self, ctx: commands.Context, game_link: str):
        if not await has_approval_perms(ctx, 3):
            return
            
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        session = await active_sessions.find_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "status": "active"})
        if session:
            return await ctx.send("A session is already active in this channel. Please end it to start a new one!", ephemeral=True)

        view = VCChannelSelectView(game_link, ctx.author)
        await ctx.send(view=view)
    
    @session.command(name="cancel", description="Cancel the current session in this channel (Central Command+)", extras={'category': 'Sessions'})
    async def session_cancel(self, ctx: commands.Context, *, reason: str):
        await ctx.defer(ephemeral=True)
        if not await has_approval_perms(ctx, 3):
            return
        
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        session = await active_sessions.find_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "status": "waiting"})
        if not session:
            return await ctx.send("No waiting session found in this channel.", ephemeral=True)

        await active_sessions.update_one(
            {"_id": session["_id"]},
            {"$set": {"status": "cancelled"}}
        )

        message_id = session.get("message_id")
        try:
            message = await ctx.channel.fetch_message(message_id)
            await ctx.send("Message Found", ephemeral=True, delete_after=5)
        except discord.NotFound:
            embed = discord.Embed(title="Message not found", description="", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        await message.reply(f"Session cancelled by <@{ctx.author.id}> for the following reason:\n\n{reason}")

    @session.command(name="end", description="End the current session in this channel (Central Command+).", extras={'category': 'Sessions'})
    async def session_end(self, ctx: commands.Context):
        if not await has_approval_perms(ctx, 3):
            return
            
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        session = await active_sessions.find_one({"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "status": "active"})
        if not session:
            return await ctx.send("No active session found in this channel.", ephemeral=True)
        
        session_end = datetime.now(UTC)
        
        await active_sessions.update_one(
            {"_id": session["_id"]},
            {
                "$set": {
                    "status": "ended",
                    "ended_at": session_end
                }
            }
        )

        embed = discord.Embed(title="Session Ended", description=f"The session hosted by <@{session['host_id']}> has ended.", color=discord.Color.green())
        await ctx.send(embed=embed)

        await self._cleanup_user(session, session_end)

        session = await active_sessions.find_one({"_id": session["_id"]})

        # Main embed: overall session info + reactions
        green_list = session.get("rsvp", {}).get("green", [])
        yellow_list = session.get("rsvp", {}).get("yellow", [])

        main_embed = discord.Embed(
            title="Session Report",
            description=f"> **Session ID: **{session['_id']}\n"
                        f"> **Host: **<@{session['host_id']}>\n"
                        f"> **Game Link: **{session.get('game_link', 'N/A')}\n"
                        f"> **Started: **{discord.utils.format_dt(session.get('started_at')) if session.get('started_at') else "Unknown"}\n"
                        f"> **Ended: **{discord.utils.format_dt(session.get('ended_at')) if session.get('ended_at') else "Unknown"}",
            color=discord.Color.light_grey()
        )

        reacted_value = (
            f"\U0001F7E9: {', '.join(green_list) or 'None'}\n"
            f"\U0001F7E8: {', '.join(yellow_list) or 'None'}"
        )
        main_embed.add_field(name="Reactions", value=reacted_value, inline=False)

        # Attendance embed: one line per user with discord timestamps
        att_lines = []
        attendance = session.get("attendance", {})
        for user_id, info in attendance.items():
            first = self._fallback_first_joined(info, session)
            last = self._fallback_last_left(info, session, session.get("ended_at"))
            total_seconds = int(info.get("total_seconds", 0))
            minutes = round(total_seconds / 60)
            periods = len(info.get("periods") or [])

            first_ts = discord.utils.format_dt(first) if first else "Unknown"
            last_ts = discord.utils.format_dt(last) if last else "Unknown"

            att_lines.append(f"<@{user_id}> {first_ts} -> {last_ts} ({minutes} minutes | {periods} periods)")

        # Ensure not exceeding embed description limit (4096). Truncate if necessary.
        desc = "\n".join(att_lines)
        if len(desc) > 4000:
            kept_lines = []
            cur_len = 0
            for line in att_lines:
                if cur_len + len(line) + 1 > 4000:
                    break
                kept_lines.append(line)
                cur_len += len(line) + 1
            remaining = len(att_lines) - len(kept_lines)
            if remaining > 0:
                kept_lines.append(f"... +{remaining} more")
            desc = "\n".join(kept_lines)

        att_embed = discord.Embed(
            title="Session Attendance",
            description=desc or "No attendance recorded.",
            color=discord.Color.light_grey()
        )

        host = self.bot.get_user(session["host_id"])
        if host:
            try:
                await host.send(embeds=[main_embed, att_embed])
            except discord.Forbidden:
                await ctx.send("I could not send this to your dms, but here is the attendance report:", embeds=[main_embed, att_embed], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))
