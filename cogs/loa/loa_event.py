import discord
from discord.ext import commands, tasks
from utils.constants import loa, loa_channel
from datetime import datetime

class LOAEvent(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @tasks.loop(minutes=1)
    async def check_loa_end_date(self):
        all_active_loas = await loa.find().to_list(length=None)

        for loa_record in all_active_loas:
            current_datetime = datetime.now()

            guild: discord.Guild = await self.bot.get_guild(loa_record.get('guild_id'))
            channel: discord.TextChannel = await guild.fetch_channel(loa_channel)
            user: discord.User = await self.bot.fetch_user(loa_record.get('user_id'))

            if current_datetime > loa_record.get('end_date'):
                log_embed = discord.Embed(
                title="LOA Ended",
                description=f"**User: ** <@{user.mention}>\n**Start Time: ** {discord.utils.format_dt(loa_record.get('start_date'))}\n**End Date: ** {discord.utils.format_dt(loa_record.get('end_date'))}\n**End Reason: ** Auto Ended",
                color=discord.Color.light_grey()
            )

            await channel.send(embed=log_embed)

            await user.send(f"Your LOA in **{guild.name}** has **ENDED**!")

async def setup(bot: commands.Bot):
    await bot.add_cog(LOAEvent(bot))