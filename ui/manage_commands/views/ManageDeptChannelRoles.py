import discord
from discord import ui
from discord.ext import commands
from utils.utils import interaction_check
from utils.constants import departments

class ManageDeptReturnButton(ui.Button):
    def __init__(self, bot, user, department_doc, parent_view):
        super().__init__(label="Return", style=discord.ButtonStyle.secondary)
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        view = ManageDeptChannelRolesView(self.bot, self.user, self.department_doc, self.parent_view)
        await interaction.response.edit_message(view=view)

class ManageChannel(ui.ChannelSelect):
    def __init__(self, bot, user, department_doc, parent_view, select_type, label, value):
        super().__init__(
            min_values=1,
            max_values=1,
            placeholder="Channel/Role",
            channel_types=[select_type]
        )
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view
        self.label = label
        self.value = value
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        interaction_check(self.user, interaction.user)
        selected_option = self.values[0]

        await departments.update_one({"display_name": self.department_doc.get("display_name"), "name": self.department_doc.get("name")}, {"$set": {self.value: int(selected_option.id)}}, upsert=True)
        self.department_doc[self.value] = int(selected_option.id)

        await interaction.followup.send("Updated successfully!", ephemeral=True)

        view = ManageDeptChannelRolesView(self.bot, self.user, self.department_doc, self.parent_view)
        await interaction.edit_original_response(view=view)

class ManageRole(ui.RoleSelect):
    def __init__(self, bot, user, department_doc, parent_view, label, value):
        super().__init__(
            min_values=1,
            max_values=1,
            placeholder="Channel/Role",
        )
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view
        self.label = label
        self.value = value
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        interaction_check(self.user, interaction.user)
        selected_option = self.values[0]


        await departments.update_one({"display_name": self.department_doc.get("display_name"), "name": self.department_doc.get("name")}, {"$set": {self.value: int(selected_option.id)}}, upsert=True)
        self.department_doc[self.value] = int(selected_option.id)

        await interaction.followup.send(f"{self.label} has been updated successfully!", ephemeral=True)

        view = ManageDeptChannelRolesView(self.bot, self.user, self.department_doc, self.parent_view)
        await interaction.edit_original_response(view=view)

class ManageDeptChannelRolesSelect(ui.Select):
    def __init__(self, bot, user, department_doc, parent_view):
        super().__init__(
            min_values=1,
            max_values=1,
            placeholder="What would you like to change?",
            options=[
                discord.SelectOption(label="Promotion Request Channel", value="promo_request_channel"),
                discord.SelectOption(label="Points Request Channel", value="points_request_channel"),
                discord.SelectOption(label="Enlistment Request Channel", value="request_channel"),
                discord.SelectOption(label="First Rank", value="first_rank_id"),
                discord.SelectOption(label="Overall Rank", value="role_id"),
            ]
        )
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        selected_option = self.values[0]

        if selected_option in("promo_request_channel", "points_request_channel", "request_channel") :
            select_type = discord.ChannelType.text
        elif selected_option in ("first_rank_id", "role_id"):
            select_type = "role"

        if select_type == "role":
            action_row = ui.ActionRow(
                ManageRole(self.bot, self.user, self.department_doc, self.parent_view, selected_option.replace("_", " ").title(), selected_option)
            )
            return_button = ui.ActionRow(ManageDeptReturnButton(self.bot, self.user, self.department_doc, self.parent_view))

            container = ui.Container(
                ui.TextDisplay(f"Select the new **{selected_option.replace('_', ' ').title()}** for {self.department_doc.get('display_name')}."),
                ui.TextDisplay(f"Current {selected_option.replace('_', ' ').title()}: <@&{self.department_doc.get(selected_option, 0)}>"),
                ui.Separator(),
                action_row,
                return_button,
                accent_color=discord.Color.light_grey()
            )
            view = ui.LayoutView()
            view.add_item(container)
            await interaction.response.edit_message(view=view)
        else:
            action_row = ui.ActionRow(
                ManageChannel(self.bot, self.user, self.department_doc, self.parent_view, select_type, selected_option.replace("_", " ").title(), selected_option)
            )
            return_button = ui.ActionRow(ManageDeptReturnButton(self.bot, self.user, self.department_doc, self.parent_view))

            container = ui.Container(
                ui.TextDisplay(f"Select the new **{selected_option.replace('_', ' ').title()}** for {self.department_doc.get('display_name')}."),
                ui.TextDisplay(f"Current {selected_option.replace('_', ' ').title()}: <#{self.department_doc.get(selected_option, 0)}>"),
                ui.Separator(),
                action_row,
                return_button,
                accent_color=discord.Color.light_grey()
            )
            view = ui.LayoutView()
            view.add_item(container)
            await interaction.response.edit_message(view=view)


class ManageDeptChannelRolesView(ui.LayoutView):
    def __init__(self, bot, user, department_doc, parent_view):
        super().__init__()
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view

        action_row = ui.ActionRow(ManageDeptChannelRolesSelect(bot, user, department_doc, self))
        container = ui.Container(
            ui.TextDisplay(f"## {department_doc.get("display_name")} Department Channels and Roles"),
            ui.Separator(),
            ui.TextDisplay("**Promotion Request Channel: **This channel is where all promotion requests are sent to.\n"
                           "**Points Request Channel: **This channel is where all points requests are sent to.\n"
                           "**Request Channel: **This is where all enlistment requests are sent to.\n"
                           "**First Rank: **This is the first rank that the members of this department will receive\n"
                           "**Overall Rank: **This is the overall role that members of this department will receive."),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )
        self.add_item(container)