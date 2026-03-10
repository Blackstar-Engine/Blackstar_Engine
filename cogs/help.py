import discord
from discord.ext import commands
from datetime import datetime

class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Get help with commands")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(title="Help Command",
                              description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                                            "> `!help` - This command\n\n"
                                            "> `!execute @User` - Timeout for 10 seconds **(Wolf Only Command)**\n\n"
                                            "> `!embed text` - Custom Embed **(Wolf Only Command)**\n\n"
                                            "> `!join #channel(Optional)` - Add bot to VC to enable TTS\n\n"
                                            "> `!leave` - Remove bot from VC to disable TTS\n\n"
                                            "> `!send-reactions` - Send Reaction Roles **(Foundation Only Command)**\n\n"
                                            "> `!promotion request <department> proof(Channel Link)` - Send a promotion request\n\n"
                                            "> `!profile` - View your profile\n\n"
                                            "> `!points request <amount> proof` - Send a points requests\n\n"
                                            "> `!manage auto_reply` - Manage all server auto replys **(Foundation & Site Command Locked)**\n\n"
                                            "> `!manage profile` - Manage a users profile **(Foundation & Site Command Locked)**\n\n"
                                            "> `!loa request time(ex. 1w2d) reason` - Send an LOA request\n\n"
                                            "> `!loa manage @User(Optional)` - Manage your own or another users LOA\n\n"
                                            "> `!loa active` - See all active LOAs **(Foundation & Site Command Locked)**\n\n"
                                            "> `!enlistment request` - Request to join a department\n\n"
                                            "> `!roleuser @user department` - Give user the overall and first rank for that department, DMs that person\n\n"
                                            "> `!dm_punish @user <text>` - Notifies a user that disciplinary action has been taken against them **(Junior Mod and Central Command+)**\n\n"
                                            "> `!say <text>` - Makes the bot say a message of your choosing **(Wolf Only Command)**\n\n"
                                            "> `!send_votes` - Pings everyone who reacted with a checkmark to a training. **(Central Command+)**"
                                            ,
                              color=discord.Color.light_grey())
        embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCommand(bot))