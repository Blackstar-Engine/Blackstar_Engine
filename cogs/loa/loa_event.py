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

            # Channel (cached first)
            channel = guild.get_channel(loa_channel)
            if not channel:
                try:
                    channel = await guild.fetch_channel(loa_channel)
                except discord.NotFound:
                    await self._cleanup_record(record)
                    continue

            member = guild.get_member(record["user_id"])
            user = member or self.bot.get_user(record["user_id"])

            if not user:
                try:
                    user = await self.bot.fetch_user(record["user_id"])
                except discord.NotFound:
                    await self._cleanup_record(record)
                    continue

            # Remove LOA role
            role = guild.get_role(loa_role)
            if role and member:
                try:
                    await member.remove_roles(
                        role,
                        reason="LOA expired"
                    )
                except discord.Forbidden:
                    pass

            # Log embed
            embed = discord.Embed(
                title="LOA Ended",
                description=(
                    f"**User:** {user.mention}\n"
                    f"**Start Time:** {discord.utils.format_dt(record.get('start_date'))}\n"
                    f"**End Date:** {discord.utils.format_dt(record.get('end_date'))}\n"
                    f"**End Reason:** Auto Ended"
                ),
                color=discord.Color.light_grey()
            )

            await channel.send(embed=embed)

            # DM user
            try:
                await user.send(
                    f"Your LOA in **{guild.name}** has **ENDED**!"
                )
            except discord.Forbidden:
                pass

            await self._cleanup_record(record)

    async def _cleanup_record(self, record: dict):
        """Archive and delete an LOA record safely."""
        await stored_loa.insert_one(record)
        await loa.delete_one({"_id": record["_id"]})

    @check_loa_end_date.before_loop
    async def before_check_loa_end_date(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(LOAEvent(bot))
