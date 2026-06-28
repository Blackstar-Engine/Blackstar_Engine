import discord
from discord.ext import commands
from utils.constants import departments
from utils.utils import fetch_profile
from ui.enlistment_request.views.EnlistmentRequestSelect import EnlistmentRequestSelect

class DepartmentRequest(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group()
    async def enlistment(self, ctx: commands.Context):
        return
        
    @enlistment.command(name="request", description="Send a request to join a department", extras={'category': 'Profiles'})
    async def enlistment_request(self, ctx: commands.Context):
        profile = await fetch_profile(ctx)
        if not profile:
            return
        
        all_departments = await departments.find(
            {"is_private": False}
        ).to_list(length=None)

        dept_map = {d["display_name"]: d for d in all_departments}

        options = []
        restricted_departments = ["ISD", "IA", "ScD", "RRT", "SCD", "MTF:A-1"]

        disallow_mtf = False
        for dept, info in profile["unit"].items():
            if info["is_active"] and dept.startswith("MTF:"):
                disallow_mtf = True
                break

        for dept in dept_map:
            dept = str(dept)
            
            if dept in restricted_departments:
                continue
            # If they have the unit in there profile
            # and the unit is active, ignore it,
            # if its not active, add it
            elif profile["unit"].get(dept, False) and profile["unit"][dept]["is_active"]:
                continue
            
            # if they have an MTF dept with in there profile
            # ignore all MTF units
            elif dept.startswith("MTF:") and disallow_mtf:
                continue
            else:
                options.append(discord.SelectOption(label=dept))
        
        view = EnlistmentRequestSelect(ctx.author, options, profile)

        await ctx.send(view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DepartmentRequest(bot))