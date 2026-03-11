import discord
from discord.ext import commands
from utils.constants import MESSAGE_CODE_RE
from utils.utils import has_approval_perms, fetch_id

class Sessions(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="send_votes", description="End the vote and send the reacted users")
    async def send_votes(self, ctx: commands.Context, vc_channel: discord.VoiceChannel, game_link: str):
        result = await has_approval_perms(ctx.author, 3)
        if not result:
            return await ctx.send("You need to be apart of either foundation, site, or high command to manage another user", ephemeral=True)
            
        if ctx.message:
            await ctx.message.delete()

        results = await fetch_id(ctx.guild.id, ["sessions_channel_id", "event_channel_id", "mission_channel_id", "training_channel_id"])

        valid_channels = [results["sessions_channel_id"], results["event_channel_id"], results["mission_channel_id"], results["training_channel_id"]]
        if ctx.channel.id not in valid_channels:
            return
        
        target_message: discord.Message = None

        try:
            history = ctx.channel.history(limit=25)
        except discord.RateLimited:
            return await ctx.send("Ratelimted: Please wait for 1 minute than try again!", ephemeral=True)

        async for message in history:
            if MESSAGE_CODE_RE.search(message.content):
                target_message = message
                break
        
        if not target_message:
            return await ctx.send("Message Not Found!", ephemeral=True)
        
        
        unique_users = set()

        for reaction in target_message.reactions:
            if str(reaction.emoji) == "🟩":
                async for user in reaction.users():
                    if not user.bot:
                        unique_users.add(user.mention)
                break

        if not unique_users:
            return await ctx.send("No Voters Found!", ephemeral=True)
        
        await target_message.clear_reactions()

        mentioned_str = ", ".join(unique_users)

        await target_message.reply(f"**We are starting, please join {vc_channel.mention}**\n{game_link}\n\n{mentioned_str}")
            



async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))