import discord
from discord.ext import commands
from utils.constants import profiles, departments
from ui.points.views.AcceptDenyButtons import AcceptDenyButtons
from ui.points.views.UnitSelect import UnitSelectView


class Points(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="points")
    async def points(self, ctx: commands.Context):
        return

    @points.command(name="request", description="Request points to be added to your profile")
    async def request(self, ctx: commands.Context, points: float, channel):
        if points <= 0 or not isinstance(points, float):
            await ctx.send("Please make sure the number is positive and is an number.", ephemeral=True)
        
        embed=discord.Embed(title="Points Requested", 
                            description=f"**{points}** point(s) have been successfully requested!",
                            color=discord.Color.green())
        
        profile = await profiles.find_one({"guild_id": ctx.guild.id, "user_id": ctx.author.id})

        options = []
        units = dict(profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                options.append(discord.SelectOption(label=unit))
        
        if options == []:
            options.append(discord.SelectOption(label="No Active Units", value="no_units"))

        unit_select_view = UnitSelectView(self.bot, options, profile)
        unit_select_embed = discord.Embed(title="Select a Unit", description="Please select a unit you would like this point request to send to!", color=discord.Color.light_grey())

        await ctx.send(embed=unit_select_embed, view=unit_select_view, ephemeral=True)

        await unit_select_view.wait()

        dept = unit_select_view.dept

        if dept == "no_unit":
            await ctx.send("You do not have any active units to send this request to.", ephemeral=True)
            return

        channel_id = await departments.find_one({"display_name": dept})

        channel_var = ctx.guild.get_channel(int(channel_id.get("points_request_channel")))

        mod_embed = discord.Embed(title="New Points Request",
                                  description=f"**User: ** {ctx.author.mention}\n** Requested Points: ** {points}\n**Proof: ** {channel}",
                                  color=discord.Color.light_grey())
        
        current_points = profile['unit'][dept].get('current_points', 0)
        total_points = profile['unit'][dept].get('total_points', 0)

        
        
        mod_embed.add_field(name="__Profile Info:__",
                            value=f"> **Codename: ** {profile.get('codename')}\n> **Join Date: ** {profile.get('join_date')}\n> **{dept} Current Points: ** {current_points}\n> **{dept} Total Points: ** {total_points}")


        accept_deny_buttons_view = AcceptDenyButtons(self.bot, ctx.author, points, mod_embed, profile, dept)

        await channel_var.send(embed=mod_embed, view=accept_deny_buttons_view)

        await ctx.send(embed=embed, delete_after=10, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Points(bot))