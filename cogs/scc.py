import discord
from discord.ext import commands
from ui.SCC.views.SCCManage import CombatMain
from utils.constants import combat_profiles, combat_classes
from datetime import timedelta, datetime

class SCC(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="scc")
    async def SCC(self, ctx: commands.Context):
        return

    @SCC.command(name="manage", description="Manage a user's combat classification.", extras={'category': 'Combat'})
    async def scc_manage(self, ctx: commands.Context, user: discord.Member):
        documents = await combat_classes.find().to_list(length=None)
        view = CombatMain(documents, user)

        await ctx.send(view=view, ephemeral=True)
    
    @SCC.command(name="profile", description="View your SCC profile", extras={'category': 'Combat'})
    async def scc_profile(self, ctx: commands.Context):
        profile = await combat_profiles.find_one({"user_id": ctx.author.id}) or {}

        categories = {
            "overall": "Overall Ranking",
            "short_range": "Short Range",
            "long_range": "Long Range",
            "teamwork": "Teamwork & Coordination",
            "leadership": "Leadership",
            "gamesense": "Game Sense",
            "movement": "Movement"
        }

        lines = []

        for key, name in categories.items():
            rank = profile.get(key, "Unranked")
            lines.append(f"**{name}**: {rank}")

        embed = discord.Embed(
            title="SCC Rank Profile",
            description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"+ "\n".join(lines),
            color=discord.Color.light_gray()
        )
        embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await ctx.send(embed=embed)
        

async def setup(bot):
    await bot.add_cog(SCC(bot))