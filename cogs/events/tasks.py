import discord
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
    
    async def _handle_sessions(self, all_sessions: dict, now: datetime, use_date: str, session_type: str, end_style: str, hours: int):
        for session in all_sessions:
            date = session.get(use_date)

            if date and date.tzinfo is None:
                date = date.replace(tzinfo=UTC)
            
            if date and (now - date).total_seconds() >= hours * 3600:
                guild = self.bot.get_guild(session.get("guild_id", 0))
                if not guild:
                    continue

                host = guild.get_member(session.get("host_id", 0))
                channel = await self._fetch_channel(guild, session.get("channel_id", 0))
                if not channel:
                    continue

                try:
                    message = await channel.fetch_message(session.get("message_id", 0))
                except Exception:
                    continue

                embed = discord.Embed(
                        title=f"{session_type.title()} Session Reminder",
                        description=f"Hello, you have a session thats been active for over {hours} hours\n\n"
                                f"> **Session Server: **{guild.name}\n"
                                f"> **Session Channel: **{channel.mention}\n"
                                f"> **Session Message: **{message.jump_url}\n\n" 
                                "Please end this session if its no longer active or if it has concluded!",
                        color=discord.Color.yellow()
                    )

                view = EndCancelSessionView(session, end_style)
                if isinstance(host, discord.Member):
                    try:
                        await host.send(embed=embed, view=view)
                        continue
                    except Exception:
                        pass

                try:
                    await channel.send(content=f"<@{session.get('host_id', 0)}>", embed=embed, view=view)
                except Exception:
                    pass

    @tasks.loop(hours=1)
    async def session_reminders(self):
        now = datetime.now(UTC)
        
        all_active_sessions = await active_sessions.find({"status": "active"}).to_list(length=None)
        all_waiting_sessions = await active_sessions.find({"status": "waiting"}).to_list(length=None)
        
        if all_active_sessions:
            await self._handle_sessions(all_active_sessions, now, "started_at", "active", "ended", 4)
                    
        if all_waiting_sessions:
            await self._handle_sessions(all_waiting_sessions, now, "created_at", "waiting", "cancelled", 2)
        

    @tasks.loop(time=birthday_run_time)
    async def birthday(self):
        if constants.ENVIRONMENT == "PRODUCTION":
            guild_id = 1411941814923169826
        else:
            guild_id = 1450297281088720928

        today = datetime.now(timezone.utc).strftime("%m-%d")

        async for birthday in birthdays.find({"date": today}):
            await self._send_birthday_message(guild_id, birthday)

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

        if not expired_loas and not expired_roas:
            return

        loa_config_cache = {}
        roa_config_cache = {}

        await self._process_expired_records(expired_roas, roa_config_cache, "roa", "ROA")
        await self._process_expired_records(expired_loas, loa_config_cache, "loa", "LOA")

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
        if member:
            return member

        try:
            member = await guild.fetch_member(user_id)
            return member
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return user_id

    async def _send_birthday_message(self, guild_id: int, birthday: dict):
        user = None
        try:
            user = await self.bot.fetch_user(birthday["user_id"])
            results = await fetch_id(guild_id, "birthdays")
            if not results or not results.get("values"):
                raise ValueError("Missing birthday channel/role configuration")

            channel_id = results["values"].get("channel")
            role_id = results["values"].get("role")
            if channel_id is None or role_id is None:
                raise ValueError("Birthday channel or role not configured")

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                raise ValueError("Birthday channel not found")

            embed = discord.Embed(
                color=16087715,
                title="🎉 Happy Birthday!",
                description=f"Today is {user.mention}'s birthday, be sure to wish them a happy birthday!",
            )

            await channel.send(content=f"<@&{role_id}>", embed=embed)
        except Exception as e:
            fallback_channel = self.bot.get_channel(1464811075760427008)
            user_repr = user.mention if user else f"<@{birthday['user_id']}>"
            if fallback_channel:
                await fallback_channel.send(f"Failed to post {user_repr}'s birthday;\n```py{e}```")

    async def _process_expired_records(self, records: list[dict], config_cache: dict, config_type: str, record_type: str):
        for record in records:
            guild_id = record.get("guild_id")
            if not guild_id:
                continue

            if guild_id not in config_cache:
                config_cache[guild_id] = await fetch_id(guild_id, config_type)
            config = config_cache[guild_id]
            if not config or not config.get("values"):
                continue

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            channel = await self._fetch_channel(guild, config["values"].get('channel'))
            member = await self._fetch_member(guild, record.get("user_id"))

            if isinstance(member, discord.Member):
                role = guild.get_role(config["values"].get('role'))
                try:
                    await member.remove_roles(role, reason=f"{record_type} expired")
                except (discord.Forbidden, AttributeError):
                    pass

            await self._preform_final_action(member, record, channel, guild, record_type)

    async def _send_expiration_embed(self, channel: discord.TextChannel | None, member: discord.Member | int, embed: discord.Embed):
        if channel is None:
            return

        try:
            if isinstance(member, discord.Member):
                await channel.send(embed=embed)
            else:
                await channel.send(content=f"<@{member}>", embed=embed)
        except discord.Forbidden:
            pass

    async def _notify_expired_user(self, member: discord.Member | int, guild: discord.Guild, record_type: str, record: dict | None = None):
        if not isinstance(member, discord.Member):
            return

        try:
            await member.send(f"Your {record_type} in **{guild.name}** has **ENDED**!")
        except discord.Forbidden:
            pass

        if record is None:
            return

        try:
            await member.edit(nick=record.get("nickname"))
        except discord.Forbidden:
            pass

    async def _preform_final_action(self, member: discord.Member | int, record: dict, channel: discord.TextChannel, guild: discord.Guild, record_type: str):
        try:
            user_id = member.id if isinstance(member, discord.Member) else member
            await profiles.update_one({"user_id": user_id, "guild_id": guild.id}, {"$set": {"status": "Active"}})
        except Exception:
            pass

        user_mention = member.mention if isinstance(member, discord.Member) else f"<@{member}>"
        embed = discord.Embed(
            title=f"{record_type} Ended",
            description=(
                f"**User:** {user_mention}\n"
                f"**Start Time:** {discord.utils.format_dt(record.get('start_date'))}\n"
                f"**End Date:** {discord.utils.format_dt(record.get('end_date'))}\n"
                f"**Reason:** Auto Ended"
            ),
            color=discord.Color.light_grey()
        )

        await self._send_expiration_embed(channel, member, embed)
        await self._notify_expired_user(member, guild, record_type, record)

        if record_type == "LOA":
            await self._cleanup_loa_record(record)
        else:
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
