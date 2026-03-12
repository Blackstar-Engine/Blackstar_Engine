import discord
from discord.ext import commands
from utils.utils import fetch_id
class DevTestingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ["annoucement_role_id", "chat_revive_role_id", "dpr_display_role_id", "game_night_role_id", "misc_role_id", "question_role_id", "raid_role_id", "session_role_id", "vote_role_id"])
        print(results)

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))