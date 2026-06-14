import discord
from discord import guild
from discord.ext import commands, tasks
from datetime import datetime, timezone, time, UTC
from utils.constants import loa, stored_loa, roa, stored_roa, BlackstarConstants, logger, profiles, birthdays, active_sessions
from utils.utils import fetch_id

constants = BlackstarConstants()

utc = timezone.utc 
enlistment_reminder_run_time = time(hour=20, minute=00, tzinfo=utc) 
birthday_run_time = time(hour=14, minute=00, tzinfo=utc)

class EndCancelSessionView(discord.ui.View):
    def __init__(self, session: dict, session_type: str):
        super().__init__(timeout=None)
        self.session = session
        self.session_type = session_type

    @discord.ui.button(label="End Session", style=discord.ButtonStyle.red, custom_id="end_session_button")
    async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        session = await active_sessions.find_one({"_id": self.session.get("_id")})
        if not session:
            await interaction.response.send_message("Session not found or already ended/cancelled.", ephemeral=True)
            return
        
        # Here you would add any additional logic needed to properly end the session
        await active_sessions.update_one({"_id": self.session.get("_id")}, {"$set": {"status": self.session_type}})
        await interaction.response.send_message(f"Session has been {self.session_type}.", ephemeral=True)

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

        self.session_reminders.start()
        if self.session_reminders.is_running():
            logger.info("Session Reminders is running.")
        else:
            logger.error("Session Reminders is not running!")

        self.birthday.start()
        if self.birthday.is_running():
            logger.info("Birthdays is running.")
        else:
            logger.error("Birthdays is not running!")
    
    def cog_unload(self):
        self.check_loa_end_date.cancel()
        self.enlistment_reminder.cancel()
        self.session_reminders.cancel()
        self.birthday.cancel()
    
    @tasks.loop(hours=1)
    async def session_reminders(self):
        now = datetime.now(UTC)
        all_active_sessions = await active_sessions.find({"status": "active"}).to_list(length=None)
        all_waiting_sessions = await active_sessions.find({"status": "waiting"}).to_list(length=None)
        if not all_active_sessions and not all_waiting_sessions:
            return
        
        if all_active_sessions:
            for session in all_active_sessions:
                started_at = session.get("started_at")

                if started_at and started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=UTC)

                # check to see if its been 12 hours past the started time
                if started_at and (now - started_at).total_seconds() >= 4 * 3600:
                    guild = self.bot.get_guild(session.get("guild_id", 0))
                    host = guild.get_member(session.get("host_id", 0))
                    channel = guild.get_channel(session.get("channel_id", 0))
                    message = await channel.fetch_message(session.get("message_id", 0))
                    embed = discord.Embed(
                        title="Active Session Reminder",
                        description="Hello, you have a session thats been active for over 4 hours\n\n"
                                f"> **Session Server: **{guild.name}\n"
                                f"> **Session Channel: **{channel.mention}\n"
                                f"> **Session Message: **{message.jump_url}\n\n" 
                                "Please end this session if its no longer active or if it has concluded!",
                        color=discord.Color.yellow()
                    )
                    view = EndCancelSessionView(session, "ended")
                    try:
                        await host.send(embed=embed, view=view)
                    except discord.Forbidden:
                        await channel.send(content=host.mention, embed=embed, view=view)
        

        if all_waiting_sessions:
            for session in all_waiting_sessions:
                created_at = session.get("created_at")

                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=UTC)

                # check to see if its been 1 hour past the created time
                if created_at and (now - created_at).total_seconds() >= 1 * 3600:
                    guild = self.bot.get_guild(session.get("guild_id", 0))
                    host = guild.get_member(session.get("host_id", 0))
                    channel = guild.get_channel(session.get("channel_id", 0))
                    message = await channel.fetch_message(session.get("message_id", 0))
                    embed = discord.Embed(
                        title="Waiting Session Reminder",
                        description="Hello, you have a session thats been waiting for over 1 hour\n\n"
                                f"> **Session Server: **{guild.name}\n"
                                f"> **Session Channel: **{channel.mention}\n"
                                f"> **Session Message: **{message.jump_url}\n\n" 
                                "Please cancel this session if its no longer active!",
                        color=discord.Color.yellow()
                    )
                    view = EndCancelSessionView(session, "cancelled")
                    try:
                        await host.send(embed=embed, view=view)
                    except discord.Forbidden:
                        await channel.send(content=host.mention, embed=embed, view=view)

    @tasks.loop(time=birthday_run_time)
    async def birthday(self):
        if constants.ENVIRONMENT == "PRODUCTION":
            guild_id = 1411941814923169826
        else:
            guild_id = 1450297281088720928

        today = datetime.now(timezone.utc).strftime("%m-%d")

        async for birthday in birthdays.find({"date": today}):
            try:
                user = await self.bot.fetch_user(birthday["user_id"])
                results = await fetch_id(guild_id, ["misc_announcements", "birthday_ping"])
                channel = self.bot.get_channel(results["misc_announcements"])

                embed = discord.Embed(
                    color=16087715,
                    title="🎉 Happy Birthday!",
                    description=f"Today is {user.mention}'s birthday, be sure to wish them a happy birthday!",
                )

                await channel.send(content=f"<@&{results['birthday_ping']}>", embed=embed)
            except Exception as e:
                channel = self.bot.get_channel(1464811075760427008)
                await channel.send(f"Failed to post {user.mention}'s birthday;\n```py{e}```")

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

        expired_roas = await roa.find(
            {"end_date": {"$lte": now}}
        ).to_list(length=None)

        if len(expired_loas) > 0:
            results = await fetch_id(expired_loas[0]["guild_id"], ['loa_role', 'loa_channel', 'roa_role'])
        elif len(expired_roas) > 0:
            results = await fetch_id(expired_roas[0]["guild_id"], ['loa_role', 'loa_channel', 'roa_role'])
        else:
            return
        
        for record in expired_roas:
            # Get guild, channel, and member
            guild = self.bot.get_guild(record.get("guild_id"))
            channel = await self._fetch_channel(guild, results['loa_channel'])
            member = await self._fetch_member(guild, record.get("user_id"))

            # Remove LOA role
            role = guild.get_role(results['roa_role'])
            try:
                await member.remove_roles(role, reason="ROA expired")
            except (discord.Forbidden, AttributeError):
                pass

            await self._preform_final_action(member, record, channel, guild, "ROA")

        for record in expired_loas:
            # Get guild, channel, and member
            guild = self.bot.get_guild(record.get("guild_id"))
            channel = await self._fetch_channel(guild, results['loa_channel'])
            member = await self._fetch_member(guild, record.get("user_id"))

            # Remove LOA role
            role = guild.get_role(results['loa_role'])
            try:
                await member.remove_roles(role, reason="LOA expired")
            except (discord.Forbidden, AttributeError):
                pass

            await self._preform_final_action(member, record, channel, guild, "LOA")

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
            return None
        return member

    async def _preform_final_action(self, member: discord.Member, record: dict, channel: discord.TextChannel, guild: discord.Guild, record_type: str):
        try:
            await profiles.update_one({"user_id": member.id, "guild_id": guild.id}, {"$set": {"status": "Active"}})
        except Exception:
            pass

        if record_type == "LOA":
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

            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
            
            # Notify User
            try:
                await member.send(f"Your LOA in **{guild.name}** has **ENDED**!")
            except discord.Forbidden:
                pass

            try:
                await member.edit(nick=record.get("nickname"))
            except discord.Forbidden:
                pass

            await self._cleanup_loa_record(record)
        elif record_type == "ROA":
            embed = discord.Embed(
                title="ROA Ended",
                description=(
                    f"**User:** {member.mention}\n"
                    f"**Start Time:** {discord.utils.format_dt(record.get('start_date'))}\n"
                    f"**End Date:** {discord.utils.format_dt(record.get('end_date'))}\n"
                    f"**End Reason:** Auto Ended"
                ),
                color=discord.Color.light_grey()
            )
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass
            
            # Notify User
            try:
                await member.send(f"Your ROA in **{guild.name}** has **ENDED**!")
            except discord.Forbidden:
                pass

            try:
                await member.edit(nick=record.get("nickname"))
            except discord.Forbidden:
                pass

            await self._cleanup_roa_record(record)


    async def _cleanup_loa_record(self, record: dict):
        """Archive and delete an LOA record safely."""
        await stored_loa.insert_one(record)
        await loa.delete_one({"_id": record["_id"]})
    
    async def _cleanup_roa_record(self, record: dict):
        """Archive and delete a ROA record safely."""
        await stored_roa.insert_one(record)
        await roa.delete_one({"_id": record["_id"]})

    @check_loa_end_date.before_loop
    async def before_check_loa_end_date(self):
        await self.bot.wait_until_ready()
    
    @enlistment_reminder.before_loop
    async def before_enlistment_reminder(self):
        await self.bot.wait_until_ready()
    
    @session_reminders.before_loop
    async def before_session_reminders(self):
        await self.bot.wait_until_ready()
    
    @birthday.before_loop
    async def before_birthday(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot))
