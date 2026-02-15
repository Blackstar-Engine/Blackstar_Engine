import discord
from discord.ext import commands
from utils.constants import departments
from utils.utils import fetch_profile
from ui.department_request.view.department_select import DepartmentsRequestView

class DepartmentRequest(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.hybrid_command(name="department_request", description="Send a request to join a department")
    async def department_request(self, ctx: commands.Context):
        profile = await fetch_profile(ctx)
        if not profile:
            return
        
        all_departments = await departments.find(
            {"is_private": False}
        ).to_list(length=None)

        dept_map = {d["display_name"]: d for d in all_departments}

        options = []
        restricted_departments = ["ISD", "CI", "IA", "ScD", "RRT", "SCD"]

        for dept in dept_map:
            if dept in restricted_departments:
                continue
            else:
                options.append(discord.SelectOption(label=dept))

        embed = discord.Embed(title="Department Selection", description="Please select all departments you would like to enlist to!", color=discord.Color.green())
        
        view = DepartmentsRequestView(self.bot, ctx.author, options, profile)

        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(DepartmentRequest(bot))