import discord
from discord.ext import commands
from ui.applications.ApplicationSelection import ApplicationOpen, ApplicationClose
from utils.constants import application_channels
from utils.utils import has_approval_perms

class Applications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group()
    async def applications(self, ctx: commands.Context):
        return

    @applications.command(name="open", description="Opens a private departments application")
    async def open_applications(self, ctx: commands.Context):
        if not await has_approval_perms(ctx, 6):
            return

        view = ApplicationOpen()
        embed = discord.Embed(title="Applications", description="Please select one of the following departments to open applications for.", color=discord.Color.light_gray())
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @applications.command(name="close", description="Closes a private departments application")
    async def close_applications(self, ctx: commands.Context):
        if not await has_approval_perms(ctx, 6):
            return

        view = ApplicationClose()
        embed = discord.Embed(title="Applications", description="Please select one of the following departments to close applications for.", color=discord.Color.light_gray())
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        await ctx.send(embed=embed, view=view, ephemeral=True)
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Applications(bot))
