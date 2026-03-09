import discord
from discord.ext import commands
from utils.constants import sessions_channel_id, event_channel_id, mission_channel_id, training_channel_id, MESSAGE_CODE_RE, central_command, high_command, foundation_command, site_command

class Sessions(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="send_votes", description="End the vote and send the reacted users")
    async def send_votes(self, ctx: commands.Context, vc_channel: discord.VoiceChannel, game_link: str):
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)
        high_role = await ctx.guild.fetch_role(high_command)
        central_role = await ctx.guild.fetch_role(central_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles and high_role not in ctx.author.roles or central_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation, site, or high command to manage another user", ephemeral=True)
            
        await ctx.message.delete() 
        message_code = ""

        channels = [sessions_channel_id, event_channel_id, mission_channel_id, training_channel_id]
        if ctx.channel.id in channels:
            message_code = MESSAGE_CODE_RE
        else:
            return
        
        reactions = None
        content_message: discord.Message = None

        async for message in ctx.channel.history(limit=25):
            if message_code.search(message.content):
                reactions = message.reactions
                content_message = message
                break
        
        if not reactions:
            return await ctx.send("Message Not Found!", ephemeral=True)
        
        
        mentioned_users = ""
        for reaction in reactions:
            async for user in reaction.users():
                if not user.bot:
                    mentioned_users += f"{user.mention},"
        
        await content_message.clear_reactions()

        await content_message.reply(f"**We are starting, please join {vc_channel.mention}**\n{game_link}\n{mentioned_users}")
            



async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))