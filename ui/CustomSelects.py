import discord
from discord.ext import commands
from discord import ui

class RoleView(ui.View):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a role"):
        super().__init__(timeout=None)
        self.bot = bot
        self.roles = None
        self.role_select_callback.min_values = min_values
        self.role_select_callback.max_values = max_values
        self.role_select_callback.placeholder = placeholder
    
    @ui.select(cls=discord.ui.RoleSelect)
    async def role_select_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
        self.roles = select.values
        await interaction.response.edit_message(content=f"You selected the following roles: {", ".join(role.name for role in self.roles)}", view=None, embed=None)
        self.stop()


class UserView(ui.View):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a user"):
        super().__init__(timeout=None)
        self.bot = bot
        self.users = None
        self.user_select_callback.min_values = min_values
        self.user_select_callback.max_values = max_values
        self.user_select_callback.placeholder = placeholder
    
    @ui.select(cls=discord.ui.UserSelect)
    async def user_select_callback(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        self.users = select.values
        await interaction.response.edit_message(content=f"You selected the following users: {", ".join(user.name for user in self.users)}", view=None, embed=None)
        self.stop()