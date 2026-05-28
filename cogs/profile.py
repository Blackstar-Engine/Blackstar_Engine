from discord.ext import commands
from ui.profile.modals.CreateProfile import CreateProfileModal
from ui.profile.views.UnitSelect import UnitSelectView
from ui.profile.views.CTXCreateProfileButton import CTXCreateProfileButton
from utils.utils import fetch_profile, fetch_unit_options, has_approval_perms, fetch_id, get_limit

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="View or create your profile in the server.", with_app_command=True, extras={'category': 'Profiles'})
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
            perms = await has_approval_perms(ctx, 3, False)
            if perms:
                results = await fetch_id(
                    ctx.guild.id,
                    ["central_command", "foundation_command", "high_command", "site_command"]
                )

                limit = await get_limit(ctx, results)

            # Fetch current department options
            options = fetch_unit_options(profile)

            view = UnitSelectView(self.bot, options, profile, limit if perms else None)

            await ctx.send(view=view, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))