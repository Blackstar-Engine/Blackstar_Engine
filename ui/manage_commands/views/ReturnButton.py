import discord
from discord import ui
from utils.constants import profiles
from utils.utils import fetch_unit_options, interaction_check

class ReturnButton(ui.Button):
    def __init__(self, bot, moderator: discord.Member, inacted_user: discord.Member):
        super().__init__(label="Return", style=discord.ButtonStyle.gray)
        self.moderator = moderator
        self.inacted_user = inacted_user
        self.bot = bot
    
    async def callback(self, interaction: discord.Interaction):
        from ui.manage_commands.views.ManageProfileMainView import ManageProfileMainView
        interaction_check(interaction.user, self.moderator)

        profile = await profiles.find_one({'guild_id': interaction.guild.id, 'user_id': self.inacted_user.id})
        if not profile:
            embed = discord.Embed(title="", description="Profile Not Found", color=discord.Color.dark_embed())
            await interaction.response.send_message(embed=embed)
        else:
            # Fetch active departments
            options = fetch_unit_options(profile)

            is_owner = await self.bot.is_owner(interaction.user)
            view = ManageProfileMainView(self.bot, self.moderator, self.inacted_user, profile, options, is_owner)

            await interaction.response.edit_message(view=view)
