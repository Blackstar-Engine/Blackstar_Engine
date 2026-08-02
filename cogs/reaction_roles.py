import discord
from discord.ext import commands
from ui.reaction_roles.views.RoleSelect import RoleSelect
from utils.utils import permissions
from utils.constants import BlackstarConstants

constants = BlackstarConstants()

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.hybrid_command(name="send_reactions", description="This will send an embed with all reaction roles for the server (Foundation Command+).", with_app_command=True, extras={'category': 'Administration'})
    @permissions()
    async def send_reaction_roles(self, ctx: commands.Context):        
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass

        view = RoleSelect()

        await ctx.channel.send(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect())