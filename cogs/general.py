import discord
from discord.ext import commands
from datetime import timedelta, datetime
from utils.constants import wolf_id, central_command, high_command, site_command, foundation_command, junior_mod, mod, senior_mod, staff_manager
class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="execute", description="Execute the user")
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        if ctx.author.id != wolf_id:
            return await ctx.send("You are not allowed to use this command!", ephemeral=True)

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

        await ctx.message.delete()
        
        custom_embed = discord.Embed(title="The Blackstar Corporation", description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{text}", color=discord.Color.light_grey())
        custom_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        custom_embed.set_thumbnail(url=self.bot.user.display_avatar.url)


        await ctx.send(embed=custom_embed)

    @commands.hybrid_command(name="say", description="Makes the bot say a message")
    async def say(self, ctx: commands.Context, *, text: str):
        if ctx.author.id != wolf_id:
            await ctx.send("You are not allowed to use this command!", ephemeral=True)
            return

        await ctx.message.delete()
        await ctx.send(text)


    @commands.hybrid_command(name="dm_punish", description="Notifies a user that disciplinary action has been taken")
    async def dm_punish(self, ctx: commands.Context, user: discord.Member, *, text: str):
        allowed_roles = [
            central_command,
            high_command,
            site_command,
            foundation_command,
            junior_mod,
            mod,
            senior_mod,
            staff_manager
        ]
        if any(role.id in allowed_roles for role in ctx.author.roles):
            try:
                embed = discord.Embed(title="Notice of Disciplinary Action", description=text, color=discord.Color.light_grey())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await user.send(embed=embed)
                await ctx.send(content="Message sent!", ephemeral=True)


            except discord.Forbidden:
                embed = discord.Embed(title="Error", description="The user you are attempting to DM has their direct messages turned off.", color=discord.Color.red())
                await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send("You are not allowed to use this command!", ephemeral=True)
            return
    

    
async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))