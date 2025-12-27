import discord
from discord.ext import commands
from utils.ui.paginator import PaginatorView
from utils.constants import sessions, profiles

class Sessions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="session", description="Manage sessions", with_app_command=True)
    async def session(self, ctx: commands.Context):
        profile = await profiles.find_one({"guild_id": ctx.guild.id, "user_id": ctx.author.id})

        all_sessions = await sessions.find({"guild_id": ctx.guild.id, "_id": {'$in': profile.get('sessions')}}).to_list(length=None)

        view = PaginatorView(self.bot, ctx.author, all_sessions)
        embed = view.create_record_embed()

        await ctx.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot))