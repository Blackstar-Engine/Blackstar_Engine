import discord
from discord.ext import commands
from discord import ui


def create_role_select(min_values: int, max_values: int, placeholder: str) -> discord.ui.RoleSelect:
    return discord.ui.RoleSelect(
        min_values=min_values,
        max_values=max_values,
        placeholder=placeholder,
    )


def create_user_select(min_values: int, max_values: int, placeholder: str) -> discord.ui.UserSelect:
    return discord.ui.UserSelect(
        min_values=min_values,
        max_values=max_values,
        placeholder=placeholder,
    )


def create_channel_select(
    min_values: int = 1,
    max_values: int = 1,
    placeholder: str = "Select a channel",
    types: discord.ChannelType = None,
) -> discord.ui.ChannelSelect:
    select = discord.ui.ChannelSelect(
        min_values=min_values,
        max_values=max_values,
        placeholder=placeholder,
    )
    if types:
        select.channel_types = [types]
    return select


class RoleView(ui.View):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a role"):
        super().__init__(timeout=None)
        self.bot = bot
        self.roles = None

        self.role_select = create_role_select(min_values, max_values, placeholder)
        self.role_select.callback = self.role_select_callback
        self.add_item(self.role_select)

    async def role_select_callback(self, interaction: discord.Interaction):
        select = self.role_select
        self.roles = select.values
        await interaction.response.edit_message(content=f"You selected the following roles: {", ".join(role.name for role in self.roles)}", view=None, embed=None)
        self.stop()


class UserView(ui.View):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a user"):
        super().__init__(timeout=None)
        self.bot = bot
        self.users = None

        self.user_select = create_user_select(min_values, max_values, placeholder)
        self.user_select.callback = self.user_select_callback
        self.add_item(self.user_select)

    async def user_select_callback(self, interaction: discord.Interaction):
        select = self.user_select
        self.users = select.values
        await interaction.response.edit_message(content=f"You selected the following users: {", ".join(user.name for user in self.users)}", view=None, embed=None)
        self.stop()

class ChannelView(ui.View):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a channel", types: discord.ChannelType = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.channels = None

        self.channel_select = create_channel_select(min_values, max_values, placeholder, types)
        self.channel_select.callback = self.channel_select_callback
        self.add_item(self.channel_select)

    async def channel_select_callback(self, interaction: discord.Interaction):
        select = self.channel_select
        self.channels = select.values
        await interaction.response.edit_message(content=f"You selected the following channels: {", ".join(channel.name for channel in self.channels)}", view=None, embed=None)
        self.stop()


class RoleRow(ui.ActionRow):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a role"):
        super().__init__()
        self.bot = bot
        self.roles = None
        self.role_select = create_role_select(min_values, max_values, placeholder)
        self.role_select.callback = self.role_select_callback
        self.add_item(self.role_select)

    async def role_select_callback(self, interaction: discord.Interaction):
        self.roles = self.role_select.values
        await interaction.response.edit_message(content=f"You selected the following roles: {", ".join(role.name for role in self.roles)}", view=None, embed=None)
        self.view.stop()


class UserRow(ui.ActionRow):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a user"):
        super().__init__()
        self.bot = bot
        self.users = None
        self.user_select = create_user_select(min_values, max_values, placeholder)
        self.user_select.callback = self.user_select_callback
        self.add_item(self.user_select)

    async def user_select_callback(self, interaction: discord.Interaction):
        self.users = self.user_select.values
        await interaction.response.edit_message(content=f"You selected the following users: {", ".join(user.name for user in self.users)}", view=None, embed=None)
        self.view.stop()


class ChannelRow(ui.ActionRow):
    def __init__(self, bot: commands.Bot, min_values: int = 1, max_values: int = 1, placeholder: str = "Select a channel", types: discord.ChannelType = None, on_select=None):
        super().__init__()
        self.bot = bot
        self.channels = None
        self.on_select = on_select
        self.channel_select = create_channel_select(min_values, max_values, placeholder, types)
        self.channel_select.callback = self.channel_select_callback
        self.add_item(self.channel_select)

    async def channel_select_callback(self, interaction: discord.Interaction):
        self.channels = self.channel_select.values
        if self.on_select:
            await self.on_select(interaction)
            return
        await interaction.response.edit_message(content=f"You selected the following channels: {", ".join(channel.name for channel in self.channels)}", view=None, embed=None)
        if self.view:
            self.view.stop()