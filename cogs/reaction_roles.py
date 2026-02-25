from discord.ext import commands
from ui.reaction_roles.views.RoleSelect import RoleSelect
from utils.constants import foundation_command

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="send-reactions", description="This will send an embed with all reaction roles for the server.")
    async def send_reaction_roles(self, ctx: commands.Context):
        foundation_role = await ctx.guild.fetch_role(foundation_command)

        if foundation_role not in ctx.author.roles:
            return
        
        await ctx.message.delete()

        view = RoleSelect()

        await ctx.send(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect())