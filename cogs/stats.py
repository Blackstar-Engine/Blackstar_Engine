import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="graph")
    async def points(self, ctx: commands.Context):
        return

    @points.command(name="test", description="Test graph")
    async def send_votes(self, ctx: commands.Context):
        time = [1, 2, 3, 4, 5]
        requests = [2, 6, 1, 5, 9]

        fig, ax = plt.subplots(figsize=(8,5))

        fig.set_facecolor("#1e1e1e")  
        ax.set_facecolor("#1e1e1e")  

        ax.plot(time, requests, color="#4CAF50", linewidth=6, solid_joinstyle="round", solid_capstyle="round")

        y_max = max(requests) + 5
        ax.set_yticks(range(0, y_max, 5))

        ax.set_xticks([])

        ax.tick_params(axis="y", colors="white")

        ax.set_ylabel("Point Requests", color="white")

        for spine in ax.spines.values():
            spine.set_visible(False)


        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        plt.close(fig)

        file = discord.File(buffer, filename="graph.png")
        embed = discord.Embed(title="Blackstar Corporation", color=discord.Color.light_gray())
        embed.set_image(url="attachment://graph.png")

        await ctx.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))