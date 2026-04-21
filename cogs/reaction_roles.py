from discord.ext import commands
from ui.reaction_roles.views.RoleSelect import RoleSelect
from utils.utils import has_approval_perms, fetch_id
from utils.constants import BlackstarConstants

constants = BlackstarConstants()

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="send-reactions", description="This will send an embed with all reaction roles for the server.")
    async def send_reaction_roles(self, ctx: commands.Context):
        await has_approval_perms(ctx.author, 6)
        
        await ctx.message.delete()

        view = RoleSelect()

        await ctx.send(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect())