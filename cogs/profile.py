import discord
from discord.ext import commands
from utils.constants import profiles
from ui.profile.modals.CreateProfile import CreateProfileModal
from ui.profile.views.UnitSelect import UnitSelectView
from ui.profile.views.CTXCreateProfileButton import CTXCreateProfileButton
from utils.utils import fetch_profile, fetch_unit_options

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="View or create your profile in the server.", with_app_command=True)
    async def profile(self, ctx: commands.Context):

        # Fetch the profile and check to see if they alrady have one or not
        profile = await fetch_profile(ctx, False)
        if not profile:
            # Try to send the creation as a modal, if not send a button to the channel
            try:
                modal = CreateProfileModal(self.bot)
                await ctx.interaction.response.send_modal(modal)
            except AttributeError:
                view = CTXCreateProfileButton(self.bot, ctx.author)
                await ctx.send("Please click the button to continue!", view=view)
        else:
            # Fetch current department options
            options = fetch_unit_options(profile)

            private_unit = ", ".join(profile.get('private_unit', []))

            # Create the embed, view, and send to the channel
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=ctx.author.display_avatar.url)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)

            view = UnitSelectView(self.bot, options, profile)

            await ctx.send(embed=embed, view=view, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))