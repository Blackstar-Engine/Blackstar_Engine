import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

from utils.constants import (
    loa,
    stored_loa,
    loa_channel,
    loa_role,
)


class LOAEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_loa_end_date.start()
        if self.check_loa_end_date.is_running():
            print("LOA End Date Checker is running.")
    
    def cog_unload(self):
        self.check_loa_end_date.cancel()

    @tasks.loop(minutes=1)
    async def check_loa_end_date(self):
        now = datetime.now(timezone.utc)

        # Only fetch expired LOAs
        expired_loas = await loa.find(
            {"end_date": {"$lte": now}}
        ).to_list(length=None)

        for record in expired_loas:
            guild = self.bot.get_guild(record.get("guild_id"))
            if not guild:
                await self._cleanup_record(record)
                continue

            # Get channel and member
            channel = await self._fetch_channel(guild)
            member = await self._fetch_member(guild, record.get("user_id"))

            # Remove LOA role
            role = guild.get_role(loa_role)
            if role and isinstance(member, discord.Member):
                try:
                    await member.remove_roles(role, reason="LOA expired")
                except discord.Forbidden:
                    pass

            # Log embed
            embed = discord.Embed(
                title="LOA Ended",
                description=(
                    f"**User:** {member.mention}\n"
                    f"**Start Time:** {discord.utils.format_dt(record.get('start_date'))}\n"
                    f"**End Date:** {discord.utils.format_dt(record.get('end_date'))}\n"
                    f"**End Reason:** Auto Ended"
                ),
                color=discord.Color.light_grey()
            )

            # Send Embed
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
            
            # Notify User
            try:
                await member.send(f"Your LOA in **{guild.name}** has **ENDED**!")
            except discord.Forbidden:
                pass

            await self._cleanup_record(record)

    async def _fetch_channel(self, guild: discord.Guild):
        channel = guild.get_channel(loa_channel)
        if not channel:
            try:
                channel = await guild.fetch_channel(loa_channel)
            except (discord.NotFound, discord.Forbidden):
                return None
        return channel
    
    async def _fetch_member(self, guild: discord.Guild, user_id: int):
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await self.bot.fetch_user(user_id)
            except (discord.NotFound, discord.Forbidden):
                return None
        return member

    async def _cleanup_record(self, record: dict):
        """Archive and delete an LOA record safely."""
        await stored_loa.insert_one(record)
        await loa.delete_one({"_id": record["_id"]})

    @check_loa_end_date.before_loop
    async def before_check_loa_end_date(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(LOAEvent(bot))
