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
    
    async def _cleanup_user(self, session, session_end):
        for user_id, info in session.get("attendance", {}).items():

            # JOIN TIME
            join_time = info.get("joined_at")

            if not join_time:
                join_time = session["started_at"]

            if join_time.tzinfo is None:
                join_time = join_time.replace(tzinfo=UTC)

            # LEFT TIME
            left_time = info.get("left_at")

            if not left_time:
                left_time = session_end

            if left_time.tzinfo is None:
                left_time = left_time.replace(tzinfo=UTC)

            # DURATION
            duration = (
                left_time - join_time
            ).total_seconds()

            # UPDATE DATABASE
            await active_sessions.update_one(
                {
                    "_id": session["_id"]
                },
                {
                    "$set": {
                        f"attendance.{user_id}.joined_at": join_time,
                        f"attendance.{user_id}.left_at": left_time,
                        f"attendance.{user_id}.duration": duration,
                        f"attendance.{user_id}.currently_in": False
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

        view = VCChannelSelectView(game_link, ctx.author)
        await ctx.send(view=view)
    
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

        session = await active_sessions.find_one({
            "_id": session["_id"]
        })

        lines = []

        for user_id, info in session.get("attendance", {}).items():

            joined_at = info.get("joined_at")
            left_at = info.get("left_at")

            duration = int(info.get("duration", 0))
            minutes = round(duration / 60)

            joined_text = discord.utils.format_dt(joined_at)

            left_text = discord.utils.format_dt(left_at)

            lines.append(
                f"<@{user_id}>: "
                f"{minutes} minutes "
                f"(Joined: {joined_text} | Left: {left_text})"
            )

        dm_embed = discord.Embed(
            title="Session Report",
            description=(
                f"The session in **{ctx.guild.name}** "
                "has ended this is your report.\n\n"
                "__**Reacted Users:**__\n"
                +  "\n".join(session.get("rsvp", {}).get("green", [])) + "\n"
                +  "\n".join(session.get("rsvp", {}).get("yellow", [])) + "\n"
                "__**Attendance:**__\n"
                + "\n".join(lines)
            ),
            color=discord.Color.light_grey()
        )
        dm_embed.add_field(name="Other Info",
                           value = f"**Start Time: **{discord.utils.format_dt(session['started_at'])}\n**End Time: **{discord.utils.format_dt(session['ended_at'])}\n**Game Link: **{session.get('game_link', 'N/A')}"
                           )

        host = self.bot.get_user(session["host_id"])
        if host:
            try:
                await host.send(embed=dm_embed)
            except discord.Forbidden:
                await ctx.send("I could not send this to your dms, but here is the attendance report:", embed=dm_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))