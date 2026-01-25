import discord
from discord.ext import commands

def create_dev_embed(error, guild, user, source, is_interaction):
    dev_embed = discord.Embed(title='Error', description=f'{error}', color=discord.Color.red())
    dev_embed.add_field(name="User", value=f"{user.mention} `{user.id}`", inline=False)

    if guild:
        dev_embed.add_field(name="guild", value=f"{guild.name} `{guild.id}`", inline=False)

    if not is_interaction and hasattr(source, "command"):
        dev_embed.add_field(name="Command", value=f"{source.command}", inline=False)
    
    return dev_embed

async def send_error(ctx: commands.Context, embed: discord.Embed):
    try:
        await ctx.send(embed=embed)
    except discord.Forbidden:
        pass

async def send_dev_error(bot, error, guild, user, source, is_interaction):

    dev_embed = create_dev_embed(error, guild, user, source, is_interaction)

   
    channel = await bot.fetch_channel(1464811075760427008)
    if channel:
        await channel.send(embed=dev_embed)

class OnCommandError(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        embed = discord.Embed(title='Error!', description=' ', color=discord.Color.red())

        is_interaction = isinstance(ctx, discord.Interaction)
        user = ctx.user if is_interaction else ctx.author
        guild = ctx.guild

        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"❌ Missing argument: `{error.param.name}`."

        elif isinstance(error, commands.BadArgument):
            embed.description = "❌ Invalid input. Please try again."

        elif isinstance(error, discord.NotFound):
            embed.description = "❌ Asset not found. Please Check my permissions."

        elif isinstance(error, discord.Forbidden):
            embed.description = "❌ I dont have permission to do that."

        elif isinstance(error, discord.HTTPException) and error.code == 10062:
            embed.description = "❌ Discord couldnt process that. Try again."

        elif isinstance(error, commands.MissingPermissions):
            embed.title = "Insufficient Permissions"
            embed.description = "❌ You dont have permission to do this."
            embed.color = discord.Color.orange()
        
        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = "❌ Private messages are not supported."

        elif isinstance(error, (commands.CheckFailure, commands.CommandNotFound)):
            return

        else:
            embed.description = "❌ Uh oh! An unexpected error occurred."

            await send_dev_error(self.bot, error, guild, user, error, is_interaction)
        
        await send_error(ctx, embed)
                
async def setup(bot):
    await bot.add_cog(OnCommandError(bot))