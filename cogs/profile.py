import discord
from discord.ext import commands
from utils.constants import profiles
from utils.ui.profile.modals.CreateProfile import CreateProfileModal
from utils.ui.profile.views.UnitSelect import UnitSelectView
from utils.ui.profile.views.CTXCreateProfileButton import CTXCreateProfileButton

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="View or create your profile in the server.", with_app_command=True)
    async def profile(self, ctx: commands.Context):
        profile = await profiles.find_one({'user_id': ctx.author.id, 'guild_id': ctx.guild.id})
        if not profile:
            try:
                modal = CreateProfileModal(self.bot)
                await ctx.interaction.response.send_modal(modal)
            except AttributeError:
                view = CTXCreateProfileButton(self.bot, ctx.author)
                await ctx.send("Please click the button to continue!", view=view)
        else:
            options = []
            units = dict(profile.get("unit", {}))

            for unit, data in units.items():
                if data.get("is_active"):
                    options.append(discord.SelectOption(label=unit))
            
            if options == []:
                options.append(discord.SelectOption(label="No Active Units", value="no_units"))

            private_unit = ", ".join(profile.get('private_unit', []))
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="Points", value=f"**Current Points: **{profile.get('current_points')}\n**Total Points: **{profile.get('total_points')}", inline=True)

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            view = UnitSelectView(self.bot, options, profile)

            await ctx.send(embed=embed, view=view, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))