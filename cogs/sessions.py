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
        await has_approval_perms(ctx.author, 3)
            
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        view = VCChannelSelectView(game_link, ctx.author)
        await ctx.send(view=view, ephemeral=True)
            



async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot=bot))