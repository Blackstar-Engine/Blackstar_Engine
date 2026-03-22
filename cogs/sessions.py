import discord
from discord.ext import commands
from utils.constants import MESSAGE_CODE_RE
from utils.utils import has_approval_perms, fetch_id
from ui.sessions.views.VCChannelSelect import VCChannelSelectView

class Sessions(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.hybrid_command(name="send_votes", description="End the vote and send the reacted users")
    async def send_votes(self, ctx: commands.Context, game_link: str):
        result = await has_approval_perms(ctx.author, 3)
        if not result:
            return await ctx.send("You need to be apart of either foundation, site, or high command to manage another user", ephemeral=True)
            
        if ctx.message:
            await ctx.message.delete()

        view = VCChannelSelectView(game_link, ctx.author.id)
        await ctx.send(view=view, ephemeral=True)
            



async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))