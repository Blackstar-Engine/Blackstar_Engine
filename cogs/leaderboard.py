import discord
from discord.ext import commands
from utils.constants import profiles
from ui.leaderboard.ScrollButtons import LeaderboardView

class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="leaderboard", description="Leaderboard that showcases members with the highest stats")
    async def leaderboard(self, ctx: commands.Context):

        points = []
        async for profile in profiles.find():
            units_dict = profile.get("unit", {})
            total_points = sum(unit_info.get("total_points", 0) for unit_info in units_dict.values())
            points.append((profile["user_id"], total_points))

        points.sort(key=lambda x: x[1], reverse=True)

        per_page = 10
        pages = [points[i:i + per_page] for i in range(0, len(points), per_page)]

        view = LeaderboardView(pages)
        embed = view.get_embed()
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leaderboard(bot))