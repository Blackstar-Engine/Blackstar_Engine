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
        if not await has_approval_perms(ctx.author, 6):
            return
        
        await ctx.message.delete()

        results = await fetch_id(ctx.guild.id, ["annoucement_role_id", "chat_revive_role_id", "dpr_display_role_id", "game_night_role_id", "misc_role_id", "question_role_id", "raid_role_id", "session_role_id", "vote_role_id", "external_role_id"])

        view = RoleSelect(results)

        await ctx.send(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    if constants.ENVIRONMENT == "PRODUCTION":
        guild_id = 1411941814923169826
    else:
        guild_id = 1450297281088720928
    results = await fetch_id(guild_id, ["annoucement_role_id", "chat_revive_role_id", "dpr_display_role_id", "game_night_role_id", "misc_role_id", "question_role_id", "raid_role_id", "session_role_id", "vote_role_id",  "external_role_id"])
    bot.add_view(RoleSelect(results))