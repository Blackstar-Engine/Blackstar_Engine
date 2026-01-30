import discord
from discord.ext import commands
from ui.reaction_roles.views.RoleSelect import RoleSelect

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="send-reactions", description="This will send an embed with all reaction roles for the server.")
    async def send_reaction_roles(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Blackstar Role Selection",
            description="The following are roles you can recieve notifications for: \n\n"
                        "> 📢 | **Annoucements Ping: ** Main Annoucements\n"
                        "> **Poll Ping: ** Polls\n"
                        "> **MISC Ping: ** Miscellaneous\n"
                        "> **Game Night Ping: ** Game Nights\n"
                        "> **Question Ping: ** Question of the Day\n"
                        "> **Vote Ping: ** Votes\n"
                        "> **Chat Revive Ping: ** Chat Revival\n\n"
                        "*Select a role below to add or remove the role.*",
            color=discord.Color.light_grey()
        )

        view = RoleSelect(self.bot)

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect(bot=bot))