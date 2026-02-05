import discord 
from discord.ext import commands

class tts_system_commands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    @commands.hybrid_command(name="join", description="Have the bot join your current VC.")
    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        if not channel:
            channel = ctx.author.voice.channel
        

        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.disconnect()
            await channel.connect()

        embed = discord.Embed(title="Connected!", description=f"Connected to {channel.mention}!", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    @commands.hybrid_command(name="leave", description="Have the bot leave your current VC.")
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client is not None:
            channel = ctx.voice_client.channel
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title="Disconnected!", description=f"Disconnected from {channel.mention}!", color=discord.Color.green())
            embed.set_footer(text=f"Executed by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Whoops....", description="I need be in a channel to leave!", color=discord.Color.light_grey())
            await ctx.send(embed=embed, ephemeral=True)
    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(tts_system_commands(bot))