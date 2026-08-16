import discord
from discord.ext import commands
from ui.reaction_roles.views.RoleSelect import RoleSelect
from utils.utils import permissions
from utils.constants import reaction_roles
from ui.paginator import PaginatorView
from discord.ui import Button
from ui.CustomSelects import RoleView, ChannelView

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # self.sample_doc = {
        #     "guild_id": 0,
        #     "channel_id": 0,
        #     "message_id": 0,
        #     "panel_name": "",
        #     "roles": [
        #         {
        #             "name": "",
        #             "id": 0,
        #             "emoji": ""
        #         }
        #     ]
        # }
        # Use the same presisent view tech. from point request where you use something like "reactions_{"_id"}" as the custom id
        
    # @commands.hybrid_group(name="reactions")
    # async def reactions(self, ctx: commands.Context):
    #     return

    # @reactions.command(name="list", description="List your reaction roles within this server.", with_app_command=True, extras={'category': 'Reaction Roles'})
    # @permissions()
    # async def reactions_list(self, ctx: commands.Context):
    #     guild_rr = await reaction_roles.find({"guild_id": ctx.guild.id}).to_list(length=None)
    #     view = PaginatorView(self.bot, ctx.author, guild_rr)

    #     view.update_buttons()

    #     embed = view.create_record_embed()
    #     await ctx.send(embed=embed, view=view, ephemeral=True)

    # @reactions.command(nmae="create", description="Create a new reaction role panel", with_app_command=True, extras={'category': 'Reaction Roles'})
    # async def reactions_create(self, ctx: commands.Context):
    #     return

    # @reactions.command(nmae="edit", description="Edit an existsing reaction role panel", with_app_command=True, extras={'category': 'Reaction Roles'})
    # async def reactions_edit(self, ctx: commands.Context, panel_name: str):
    #     panel = await reaction_roles.find_one({"guild_id": ctx.guild.id, "panel_name": panel_name})
    #     if not panel:
    #         await ctx.send(f"I could not find a panel by the name: `{panel_name}`")

    # @reactions.command(nmae="delete", description="Delete an existing reaction role panel", with_app_command=True, extras={'category': 'Reaction Roles'})
    # async def reactions_delete(self, ctx: commands.Context, panel_name: str):
    #     panel = await reaction_roles.find_one({"guild_id": ctx.guild.id, "panel_name": panel_name})
    #     if not panel:
    #         await ctx.send(f"I could not find a panel by the name: `{panel_name}`")
    
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