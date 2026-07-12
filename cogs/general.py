import discord
from discord.ext import commands
from datetime import timedelta, datetime
from utils.constants import profiles
from ui.leaderboard.ScrollButtons import LeaderboardView
from utils.utils import fetch_id, log_action
from ui.general.views.DmView import DMEmbedView
import random
import secrets

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _check_if_wolf(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ["wolf_id"])
        if ctx.author.id != results["wolf_id"]:
            await ctx.send("You are not allowed to use this command!", ephemeral=True)
            return False
        return True

    @commands.hybrid_command(name="execute", description="Execute the user (Wolf Only).", extras={'category': 'Administration'})
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        if not await self._check_if_wolf(ctx):
            return
        
        await log_action(ctx=ctx, log_type="mod_command", command_name="execute_user", arguments=f"user={user.mention}")

        duration = timedelta(seconds=5)
        try:
            await user.timeout(duration, reason="Execute Command")
        except discord.Forbidden:
            await ctx.send("Not Timed Out, dont have permission!", ephemeral=True)

        await ctx.send(f"{user.mention} has been executed by the order of {ctx.author.mention}!")

    @commands.hybrid_command(name="embed", description="Send an Embed (Wolf Only).", extras={'category': 'Administration'})
    async def embed(self, ctx: commands.Context, *, text: str):
        if not await self._check_if_wolf(ctx):
            return
        
        await log_action(ctx=ctx, log_type="mod_command", command_name="embed", arguments=f"text={text}")

        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        
        custom_embed = discord.Embed(title="The Blackstar Corporation", description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{text}", color=discord.Color.light_grey())
        custom_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        custom_embed.set_thumbnail(url=self.bot.user.display_avatar.url)


        await ctx.send(embed=custom_embed)

    @commands.hybrid_command(name="say", description="Makes the bot say a message (Wolf Only).", extras={'category': 'Administration'})
    async def say(self, ctx: commands.Context, *, text: str):
        if not await self._check_if_wolf(ctx):
            return
        
        await log_action(ctx=ctx, log_type="mod_command", command_name="say", arguments=f"text={text}")
        
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        
        await ctx.send(text)


    @commands.hybrid_command(name="dm_punish", description="Notifies a user that disciplinary action has been taken (Junior Mod+ and Central Command+).", extras={'category': 'Administration'})
    async def dm_punish(self, ctx: commands.Context, user: discord.Member):
        results = await fetch_id(ctx.guild.id, ["central_command",
            "high_command",
            "site_command",
            "foundation_command",
            "junior_mod",
            "mod",
            "senior_mod",
            "staff_manager"])
        
        allowed_roles = [
            results["central_command"],
            results["high_command"],
            results["site_command"],
            results["foundation_command"],
            results["junior_mod"],
            results["mod"],
            results["senior_mod"],
            results["staff_manager"]
        ]
        if any(role.id in allowed_roles for role in ctx.author.roles):
            await log_action(ctx=ctx, log_type="mod_command", command_name="dm_punish", arguments=f"user={user.mention}")
            try:
                view = DMEmbedView(self.bot, user)
                await ctx.send("Please click the button below to start creating the embed!", view=view, ephemeral=True)
            except discord.Forbidden:
                embed = discord.Embed(title="Error", description="The user you are attempting to DM has their direct messages turned off.", color=discord.Color.red())
                await ctx.send(embed=embed, ephemeral=True)
        else:
            return await ctx.send("You are not allowed to use this command!", ephemeral=True)
            
    
    @commands.hybrid_command(name="view_high", description="View all high command team members", extras={'category': 'Other'})
    async def view_high_members(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ['high_command'])
        role_obj = ctx.guild.get_role(results["high_command"])

        members = role_obj.members

        description = "\n".join(member.mention for member in members)

        embed = discord.Embed(
            title="All High Command",
            description=description,
            color=discord.Color.light_grey()
        )

        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="view_site", description="View all site command team members", extras={'category': 'Other'})
    async def view_site_members(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ['site_command'])
        role_obj = ctx.guild.get_role(results['site_command'])

        members = role_obj.members

        description = "\n".join(member.mention for member in members)

        embed = discord.Embed(
            title="All Site Command",
            description=description,
            color=discord.Color.light_grey()
        )

        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="view_foundation", description="View all foundation command team members", extras={'category': 'Other'})
    async def view_foundation_members(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ['foundation_command'])
        role_obj = ctx.guild.get_role(results['foundation_command'])

        members = role_obj.members

        description = "\n".join(member.mention for member in members)

        embed = discord.Embed(
            title="All Foundation Command",
            description=description,
            color=discord.Color.light_grey()
        )

        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="best_member", description="Who is the best member of the server?", extras={'category': 'Other'})
    async def best_member(self, ctx: commands.Context):
        server_members = ctx.guild.members
        possible_members = [member.display_name for member in server_members if not member.bot]
        possible_messages = [
            "The best member of the server is {}!",
            "The most active member of the server is {}!",
            "{} is better than wolf!",
            "The most helpful member of the server is {}!",
            "The most loyal member of the server is {}!",
            "The most trustworthy member of the server is {}!",
            "The most dedicated member of the server is {}!",
            "The most reliable member of the server is {}!",
            "The most respected member of the server is {}!",
            "The most skilled member of the server is {}!",
            "The most talented member of the server is {}!",
            "I'm sorry {}, Kaiju will always be the best member!",
            "Ethics found {} to be the best member of the server!",

        ]

        # use the cryptographically secure generator for selections
        best_member = secrets.choice(possible_members)

        message = secrets.choice(possible_messages).format(f"`{best_member}`")

        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay("# Best Member"),
            discord.ui.TextDisplay(message),
            accent_color=discord.Color.random()
        )
        view.add_item(container)

        await ctx.send(view=view, allowed_mentions=discord.AllowedMentions(users=False))

    

    
async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))