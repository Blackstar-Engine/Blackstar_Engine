import discord
from discord.ext import commands
from datetime import timedelta, datetime
from utils.constants import profiles
from ui.leaderboard.ScrollButtons import LeaderboardView
from utils.utils import fetch_id

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _check_if_wolf(self, ctx: commands.Context):
        results = await fetch_id(ctx.guild.id, ["wolf_id"])
        if ctx.author.id != results["wolf_id"]:
            await ctx.send("You are not allowed to use this command!", ephemeral=True)
            return False
        return True

    @commands.hybrid_command(name="execute", description="Execute the user")
    async def execute_user(self, ctx: commands.Context, user: discord.Member):
        if not await self._check_if_wolf(ctx):
            return

        duration = timedelta(seconds=10)
        try:
            await user.timeout(duration, reason="Execute Command")
        except discord.Forbidden:
            await ctx.send("Not Timed Out, dont have permission!", ephemeral=True)

        await ctx.send(f"{user.mention} has been executed by the order of {ctx.author.mention}!")

    @commands.hybrid_command(name="embed", description="Send an Embed")
    async def embed(self, ctx: commands.Context, *, text: str):
        if not await self._check_if_wolf(ctx):
            return

        await ctx.message.delete()
        
        custom_embed = discord.Embed(title="The Blackstar Corporation", description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n{text}", color=discord.Color.light_grey())
        custom_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        custom_embed.set_thumbnail(url=self.bot.user.display_avatar.url)


        await ctx.send(embed=custom_embed)

    @commands.hybrid_command(name="say", description="Makes the bot say a message")
    async def say(self, ctx: commands.Context, *, text: str):
        if not await self._check_if_wolf(ctx):
            return

        await ctx.message.delete()
        await ctx.send(text)


    @commands.hybrid_command(name="dm_punish", description="Notifies a user that disciplinary action has been taken")
    async def dm_punish(self, ctx: commands.Context, user: discord.Member, *, text: str):
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
            try:
                embed = discord.Embed(title="Notice of Disciplinary Action", description=text, color=discord.Color.light_grey())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await user.send(embed=embed)
                await ctx.send(content="Message sent!", ephemeral=True)


            except discord.Forbidden:
                embed = discord.Embed(title="Error", description="The user you are attempting to DM has their direct messages turned off.", color=discord.Color.red())
                await ctx.send(embed=embed, ephemeral=True)
        else:
            return await ctx.send("You are not allowed to use this command!", ephemeral=True)
            
    
    @commands.hybrid_command(name="view_high", description="View all high command team members")
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
    
    @commands.hybrid_command(name="view_site", description="View all site command team members")
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
    
    @commands.hybrid_command(name="view_foundation", description="View all foundation command team members")
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

    @commands.hybrid_command(name="leaderboard", description="Leaderboard that showcases members with the highest stats")
    async def leaderboard(self, ctx: commands.Context):

        points = []
        async for profile in profiles.find():
            units_dict = profile.get("unit", {})
            total_points = sum(unit_info.get("total_points", 0) for unit_info in units_dict.values())
            points.append((profile["user_id"], total_points))

        points.sort(key=lambda x: x[1], reverse=True)

        per_page = 10
        pages = [points[i:i + per_page] for i in range(0, len(points), per_page)]

        view = LeaderboardView(pages)
        embed = view.get_embed()
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")

        await ctx.send(embed=embed, view=view)

    

    
async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))