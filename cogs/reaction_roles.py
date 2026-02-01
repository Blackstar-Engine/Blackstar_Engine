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
                        "> <:BlackStar_Announcement:1467561153499631738> | **Annoucements Ping: ** Main Annoucements\n"
                        "> <:BlackStar_Poll:1467561281698660565> | **Poll Ping: ** Polls\n"
                        "> <:BlackStar_Miscellaneous:1467561252120166533> | **MISC Ping: ** Miscellaneous\n"
                        "> <:BlackStar_Gamenight:1467561216720240831> | **Game Night Ping: ** Game Nights\n"
                        "> <:BlackStar_QOTD:1467561311398268938> | **Question Ping: ** Question of the Day\n"
                        "> <:BlackStar_Vote:1467561338321502348> | **Vote Ping: ** Votes\n"
                        "> <:BlackStar_ChatRevive:1467561189612716205> | **Chat Revive Ping: ** Chat Revival\n\n"
                        "*Select a role below to add or remove the role.*",
            color=discord.Color.light_grey()
        )

        view = RoleSelect(self.bot)

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect(bot=bot))