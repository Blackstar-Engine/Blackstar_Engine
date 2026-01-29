import discord
from discord.ext import commands
from datetime import timedelta, datetime
from utils.constants import foundation_command, wolf_id

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="execute", description="Execute the user")
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        foundation_role = await ctx.guild.fetch_role(foundation_command)

        if foundation_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of foundation to use this command!", ephemeral=True)

        duration = timedelta(seconds=10)
        try:
            await user.timeout(duration, reason="Execute Command")
        except Exception as e:
            raise commands.CommandInvokeError(e) from e

        await ctx.send(f"{user.mention} has been executed by the order of {ctx.author.mention}!")

    @commands.hybrid_command(name="embed", description="Send an Embed")
    async def embed(self, ctx: commands.Context, *, text: str):
        if ctx.author.id != wolf_id:
            return await ctx.send("You are not allowed to use this command!", ephemeral=True)
        
        custom_embed = discord.Embed(title="The Blackstar Corporation", description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{text}", color=discord.Color.light_grey())
        custom_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        custom_embed.set_thumbnail(url=self.bot.user.display_avatar.url)


        await ctx.send(embed=custom_embed)
        

        

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))