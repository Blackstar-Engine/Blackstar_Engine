import discord
from discord.ext import commands
from ui.applications.views.ApplicationSelection import ApplicationOpen, ApplicationClose
from utils.utils import permissions, fetch_id

class Applications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group()
    async def applications(self, ctx: commands.Context):
        return

    @applications.command(name="open", description="Opens a private departments application (Foundation Command).", extras={'category': 'Administration'})
    @permissions()
    async def open_applications(self, ctx: commands.Context):
        app_channels = await fetch_id(ctx.guild.id, "application_channels")
        options = [discord.SelectOption(label=str(key.title()), value=int(value)) for key, value in app_channels["values"].items()]

        view = ApplicationOpen(options)
        embed = discord.Embed(title="Applications", description="Please select one of the following departments to open applications for.", color=discord.Color.light_gray())
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @applications.command(name="close", description="Closes a private departments application (Foundation Command).", extras={'category': 'Administration'})
    @permissions()
    async def close_applications(self, ctx: commands.Context):
        app_channels = await fetch_id(ctx.guild.id, "application_channels")
        options = [discord.SelectOption(label=str(key.title()), value=int(value)) for key, value in app_channels["values"].items()]

        view = ApplicationOpen(options)
        embed = discord.Embed(title="Applications", description="Please select one of the following departments to close applications for.", color=discord.Color.light_gray())
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        await ctx.send(embed=embed, view=view, ephemeral=True)
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Applications(bot))
