import discord
from discord.ext import commands
from utils.constants import profiles, departments, combat_classes
from ui.manage_commands.modals.EditProfile import EditProfileModal
from ui.manage_commands.views.ConfirmRemoval import ConfirmRemovalView
from ui.manage_commands.views.ManageProfileUnitsView import ProfileManageUnitsView
from ui.manage_commands.views.DepartmentButtons import DepartmentButtons
from ui.manage_commands.views.AdminTools import ManageDepartmentRow
from utils.utils import interaction_check, fetch_unit_options
from discord import ui, Interaction
import asyncio
from ui.manage_commands.views.ManageProfileViewRequests import ManageProfileViewRequests

class DepartmentSelect(ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, moderator: discord.Member, user_profile: dict, dept_options: list, node_admin: bool, is_owner: bool, nodes: dict):
        super().__init__()
        self.user_profile = user_profile
        self.bot = bot
        self.moderator = moderator
        self.user = user
        self.node_admin = node_admin
        self.is_owner = is_owner
        self.nodes = nodes

        self.role_select = ui.Select(
            placeholder="Select a Role",
            min_values=1,
            max_values=1,
            options=dept_options
        )

        self.role_select.callback = self.dept_role_select

        self.add_item(self.role_select)

    async def dept_role_select(self, interaction: discord.Interaction):
        unit = self.role_select.values[0]
        if unit == "no_units":
            return

        self.role_select.values.clear()

        options = fetch_unit_options(self.user_profile)
        view = ManageProfileMainView(bot=self.bot,
                                     user=self.user,
                                     moderator=self.moderator,
                                     user_profile=self.user_profile,
                                     user_dept_options=options,
                                     nodes=self.nodes,
                                     is_owner=self.is_owner)

        await interaction.response.edit_message(view=view)
        
        department = self.user_profile["unit"][unit]

        view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {unit} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n"
                           f"**Current Points: ** {department.get('current_points')}\n"
                           f"**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(bot=self.bot,
                              user=self.user,
                              moderator=self.moderator,
                              user_profile=self.user_profile,
                              unit=unit,
                              is_owner=self.is_owner,
                              nodes=self.nodes),
            accent_color=discord.Color.light_grey()
        )
        if self.is_owner or self.node_admin:
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.user_profile, unit))


        view.add_item(container)

        await interaction.followup.send(view=view, ephemeral=True)



class ManageProfileOptions(ui.ActionRow):
    def __init__(self, bot: commands.Bot, user: discord.Member, moderator: discord.Member, user_profile: dict, select_options: list, is_owner: bool, nodes: dict):
        super().__init__()
        self.bot = bot
        self.moderator = moderator
        self.user = user
        self.user_profile = user_profile
        self.select_options = select_options
        self.is_owner = is_owner
        self.nodes = nodes

        self.main_select = ui.Select(
            placeholder="What do you want to manage?",
            options = self.select_options,
            min_values=1,
            max_values=1
        )

        self.main_select.callback = self.main_select_callback

        self.add_item(self.main_select)

    async def view_requests(self, interaction: discord.Interaction, user: discord.Member, moderator: discord.Member, user_profile: dict):
        view = ManageProfileViewRequests(bot=self.bot,
                                         user=user,
                                         moderator=moderator,
                                         user_profile=user_profile,
                                         nodes=self.nodes
                                         )
        await interaction.response.edit_message(view=view)

    async def manage_units(self, interaction: discord.Interaction, user: discord.Member, moderator: discord.Member, user_profile: dict):
        results = await departments.find().to_list(length=None)

        user_units = []
        units = dict(user_profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                user_units.append(unit)

        user_private_units = set(user_profile.get("private_unit", []))

        normal_unit_results = []
        private_unit_results = []

        for result in results:
            unit_name = result.get("display_name")
            is_private = result.get("is_private", False)

            option = discord.SelectOption(label=unit_name)

            if is_private:
                if unit_name in user_private_units:
                    option.default = True
                private_unit_results.append(option)
            else:
                if unit_name in user_units:
                    option.default = True
                normal_unit_results.append(option)

        view = ProfileManageUnitsView(bot=self.bot,
                                      user=user,
                                      moderator=moderator,
                                      user_profile=user_profile,
                                      normal_units_results=normal_unit_results,
                                      private_units_results=private_unit_results,
                                      nodes=self.nodes
                                      )

        await interaction.response.edit_message(view=view)
        await view.wait()

        # 🔄 Reload profile after submit
        reloaded_profile = await profiles.find_one({"_id": user_profile["_id"]})

        options = fetch_unit_options(reloaded_profile)
        view = ManageProfileMainView(
            bot=self.bot,
            user=user,
            moderator=moderator,
            user_profile=reloaded_profile,
            user_dept_options=options,
            nodes=self.nodes,
            is_owner=self.is_owner
        )

        await interaction.edit_original_response(view=view)


    async def edit_profile(self, interaction: discord.Interaction, user: discord.Member, moderator: discord.Member, user_profile: dict):
        modal = EditProfileModal(self.bot, user_profile)
        await interaction.response.send_modal(modal)
        await modal.wait()

        roblox_name = modal.roblox_name.value
        timezone = modal.timezone.value
        codename = modal.codename.value
        status = modal.status.value

        user_profile["roblox_name"] = roblox_name
        user_profile["timezone"] = timezone
        user_profile["codename"] = codename
        user_profile["status"] = status.title()

        options = fetch_unit_options(user_profile)
        view = ManageProfileMainView(
            bot=self.bot,
            user=user,
            moderator=moderator,
            user_profile=user_profile,
            user_dept_options=options,
            nodes=self.nodes,
            is_owner=self.is_owner
        )

        await interaction.edit_original_response(view=view)

    async def delete_profile(self, interaction: discord.Interaction, user: discord.Member, moderator: discord.Member, user_profile: dict):
        confirm_buttons = ConfirmRemovalView(bot=self.bot, user=user, moderator=moderator, nodes=self.nodes)
        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('## Warning!'),
            ui.TextDisplay('This action is irreversible and will delete all data associated with this profile.'),
            ui.TextDisplay('Please confirm that you want to proceed with this action.'),
            ui.Separator(),
            confirm_buttons,
            accent_color=discord.Color.yellow()
        )
        view.add_item(container)
        await interaction.response.edit_message(view=view)
        await view.wait()

        if confirm_buttons.status == 1:
            await asyncio.sleep(1)
            await profiles.delete_one(user_profile)

            view = ui.LayoutView()
            container = ui.Container(
                ui.TextDisplay('Profile Has Been Deleted.'),
                accent_color=discord.Color.green()
            )
            view.add_item(container)
            await interaction.edit_original_response(view=view)
            view.stop()
    
    async def main_select_callback(self, interaction: discord.Interaction):
        interaction_check(self.moderator, interaction.user)

        if self.main_select.values[0] == "edit_profile":
            await self.edit_profile(interaction, self.moderator, self.user, self.user_profile)
        elif self.main_select.values[0] == "manage_units":
            await self.manage_units(interaction, self.moderator, self.user, self.user_profile)
        elif self.main_select.values[0] == "view_requests":
            await self.view_requests(interaction, self.moderator, self.user, self.user_profile)
        elif self.main_select.values[0] == "delete_profile":
            await self.delete_profile(interaction, self.moderator, self.user, self.user_profile)

class ManageProfileMainView(ui.LayoutView):
    def __init__(self, bot: commands.Bot, user: discord.Member, moderator: discord.Member, user_profile: dict, user_dept_options: dict, nodes: dict, is_owner: bool):
        super().__init__(timeout=300)

        private_unit = ", ".join(user_profile.get('private_unit', []))
        node_admin = nodes.get("admin", False)
        node_mod = nodes.get("mod", False)

        container = ui.Container(
            ui.TextDisplay("## Manage Profile"),
            accent_color=discord.Color.light_grey()
        )

        if is_owner or node_admin or node_mod:

            select_options = [
                discord.SelectOption(
                    label = "Edit Profile",
                    value = "edit_profile",
                    description = "Edit the user's profile",
                    emoji="<:Edit_Profile_Blackstar:1499178679417442324>"
                ), 
                discord.SelectOption(
                    label = "Manage Units",
                    value = "manage_units",
                    description = "Manage the user's units",
                    emoji="<:Manage_Units_Blackstar:1499178696773210162>"
                ),
                discord.SelectOption(
                    label = "View Requests",
                    value = "view_requests",
                    description = "View the user's requests",
                    emoji="<:View_Requests_Blackstar:1499178645699301578>"
                ),
                discord.SelectOption(
                    label = "Delete Profile",
                    value = "delete_profile",
                    description = "Delete the profile",
                    emoji="<:Delete_Profile_Blackstar:1499178664913272832>"
                )
            ]
        
            container.add_item(DepartmentSelect(bot=bot,
                                                user=user,
                                                moderator=moderator,
                                                user_profile=user_profile,
                                                dept_options=user_dept_options,
                                                node_admin=node_admin,
                                                is_owner=is_owner,
                                                nodes=nodes
                                                )
                                            )
           
        else:
            select_options = [
                discord.SelectOption(
                    label = "Edit Profile",
                    value = "edit_profile",
                    description = "Edit the user's profile",
                    emoji="<:Edit_Profile_Blackstar:1499178679417442324>"
                ), 
                discord.SelectOption(
                    label = "Manage Units",
                    value = "manage_units",
                    description = "Manage the user's units",
                    emoji="<:Manage_Units_Blackstar:1499178696773210162>"
                ),
                discord.SelectOption(
                    label = "View Requests",
                    value = "view_requests",
                    description = "View the user's requests",
                    emoji="<:View_Requests_Blackstar:1499178645699301578>"
                ),
            ]
            

        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay('### Profile Information'))
        container.add_item(ui.TextDisplay(
                                            f"**Codename: **{user_profile.get('codename')}\n"
                                            f"**Roblox Name: **{user_profile.get('roblox_name')}\n"
                                            f"**Timezone: **{user_profile.get('timezone')}\n"
                                            f"**Private Unit(s): **{private_unit}\n"
                                            f"**Join Date: ** {user_profile.get('join_date')}\n"
                                            f"**Status: ** {user_profile.get('status')}"
                                        )
                                    )
        container.add_item(ui.Separator())
        container.add_item(ManageProfileOptions(
                                                    bot=bot,
                                                    user=user,
                                                    moderator=moderator,
                                                    user_profile=user_profile,
                                                    select_options=select_options,
                                                    is_owner=is_owner,
                                                    nodes=nodes
                                                )
                                            )

        self.add_item(container)

