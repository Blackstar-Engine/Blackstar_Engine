import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, time
from utils.constants import loa, stored_loa, BlackstarConstants, logger
from utils.utils import fetch_id

constants = BlackstarConstants()

utc = timezone.utc 
enlistment_reminder_run_time = time(hour=20, minute=00, tzinfo=utc) 

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_loa_end_date.start()
        if self.check_loa_end_date.is_running():
            logger.info("LOA End Date Checker is running.")
        else:
            logger.error("LOA End Date Checker is not running!")
        
        self.enlistment_reminder.start()
        if self.enlistment_reminder.is_running():
            logger.info("Enlistment Reminders is running.")
        else:
            logger.error("Enlistment Reminders is not running!")
    
    def cog_unload(self):
        self.check_loa_end_date.cancel()
        self.enlistment_reminder.cancel()

    @tasks.loop(time=enlistment_reminder_run_time)
    async def enlistment_reminder(self):
        if constants.ENVIRONMENT == "PRODUCTION":
            guild = self.bot.get_guild(1411941814923169826)
            channel = guild.get_channel(1419346953526837411)
            thread = guild.get_channel(1433946174791876740)
            unverified_role = guild.get_role(1425314582456438924)
            unenlisted_role = guild.get_role(1452796053589065840)
            
        else:
            guild = self.bot.get_guild(1450297281088720928)
            channel = guild.get_channel(1450297998415233024)
            thread = guild.get_channel(1450298068162576525)
            unverified_role = guild.get_role(1450297879091609672)
            unenlisted_role = guild.get_role(1450297901551980555)

        embed = discord.Embed(
            title="<:BlackStar_Miscellaneous:1467561252120166533> Enlistment Reminder",
            description="Please make sure to verify and make an enlistment!"
        )

        embed.add_field(
            name="-Enlistment Process",
            value=f"> To gain access please make an enlistment request to a public department in {thread.mention}."
                "> Please reference [this thread](https://discord.com/channels/1411941814923169826/1433947466092515458) on what is avalible."
                "\n\nPlease copy this exact template\n"
                "```**Enlistment form**\n"
                "Codename:\n"
                "Discord User:\n"
                "Roblox user:\n"
                "Department: MTF/SD/MD/CD\n"
                "Unit:  E-11/NU-7/B-7\n"
                "VC: YES/NO\n"
                "Time zone:\n"
                "Reason:\n"
                "Invited from:```",
            inline=False
        )

        try:
            await channel.send(content=f"{unverified_role.mention} {unenlisted_role.mention}", embed=embed)
        except Exception as e:
            logger.error(f"Enlistment Reminder Message Failed: {e}")

    @tasks.loop(minutes=1)
    async def check_loa_end_date(self):
        now = datetime.now(timezone.utc)

        # Only fetch expired LOAs
        expired_loas = await loa.find(
            {"end_date": {"$lte": now}}
        ).to_list(length=None)

        if len(expired_loas) > 0:
            results = await fetch_id(expired_loas[0]["guild_id"], ['loa_role', 'loa_channel'])

        for record in expired_loas:
            guild = self.bot.get_guild(record.get("guild_id"))
            if not guild:
                await self._cleanup_record(record)
                continue

            # Get channel and member
            channel = await self._fetch_channel(guild, results['loa_channel'])
            member = await self._fetch_member(guild, record.get("user_id"))

            # Remove LOA role
            role = guild.get_role(results['loa_role'])
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

    async def _fetch_channel(self, guild: discord.Guild, loa_channel):
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
    await bot.add_cog(Tasks(bot))
