import discord
from discord.ext import commands
from utils.constants import profiles, departments
from ui.manage_commands.modals.EditProfile import EditProfileModal
from ui.manage_commands.views.ConfirmRemoval import ConfirmRemovalView
from ui.manage_commands.views.ManageProfileUnitsView import ProfileManageUnitsView
from ui.manage_commands.views.DepartmentButtons import DepartmentButtons
from ui.manage_commands.views.AdminTools import ManageDepartmentRow
from utils.utils import interaction_check, fetch_unit_options, has_approval_perms, fetch_id
from discord import ui, Interaction
import asyncio
from ui.manage_commands.views.ManageProfileViewRequests import ManageProfileViewRequests

class DepartmentSelect(ui.ActionRow):
    def __init__(self, bot: commands.Bot, moderator: discord.Member, inacted_user: discord.Member, profile: dict, dept_options: list):
        super().__init__()
        self.profile = profile
        self.bot = bot
        self.moderator = moderator
        self.inacted_user = inacted_user

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

        self.role_select.values.clear()

        options = fetch_unit_options(self.profile)
        is_owner = await self.bot.is_owner(interaction.user)
        view = ManageProfileMainView(self.bot, self.moderator, self.inacted_user, self.profile, options, is_owner)

        await interaction.response.edit_message(view=view)

        if unit == "no_units":
            return
        
        department = self.profile["unit"][unit]

        view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {unit} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(self.bot, self.moderator, self.inacted_user, self.profile, unit),
            accent_color=discord.Color.light_grey()
        )

        if is_owner:
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.profile, unit))
        else:
            if not await has_approval_perms(interaction, 6):
                return
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.profile, unit))

        view.add_item(container)

        await interaction.followup.send(view=view, ephemeral=True)

async def view_requests(bot: commands.Bot, interaction: discord.Interaction, moderator: discord.Member, inacted_user: discord.Member, profile: dict):
    view = ManageProfileViewRequests(bot, moderator, inacted_user, profile)
    await interaction.response.edit_message(view=view)

async def manage_units(bot: commands.Bot, interaction: discord.Interaction, moderator: discord.Member, inacted_user: discord.Member, profile: dict):
    results = await departments.find().to_list(length=None)

    user_units = []
    units = dict(profile.get("unit", {}))

    for unit, data in units.items():
        if data.get("is_active"):
            user_units.append(unit)

    user_private_units = set(profile.get("private_unit", []))

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

    view = ProfileManageUnitsView(bot, moderator, inacted_user, profile, normal_unit_results, private_unit_results)

    await interaction.response.edit_message(view=view)
    await view.wait()

    # 🔄 Reload profile after submit
    profile = await profiles.find_one({"_id": profile["_id"]})

    options = fetch_unit_options(profile)
    is_owner = await bot.is_owner(interaction.user)
    view = ManageProfileMainView(
        bot,
        moderator,
        inacted_user,
        profile,
        options,
        is_owner
    )

    await interaction.edit_original_response(view=view)


async def edit_profile(bot: commands.Bot, interaction: discord.Interaction, moderator: discord.Member, inacted_user: discord.Member, profile: dict):
    modal = EditProfileModal(bot, profile)
    await interaction.response.send_modal(modal)
    await modal.wait()

    roblox_name = modal.roblox_name.value
    timezone = modal.timezone.value
    codename = modal.codename.value
    status = modal.status.value

    profile["roblox_name"] = roblox_name
    profile["timezone"] = timezone
    profile["codename"] = codename
    profile["status"] = status.title()

    options = fetch_unit_options(profile)
    is_owner = await bot.is_owner(interaction.user)
    view = ManageProfileMainView(
        bot,
        moderator,
        inacted_user,
        profile,
        options,
        is_owner
    )

    await interaction.edit_original_response(view=view)

async def delete_profile(bot: commands.Bot, interaction: discord.Interaction, moderator: discord.Member, inacted_user: discord.Member, profile: dict):
    confirm_buttons = ConfirmRemovalView(bot, moderator, inacted_user, profile, 0)
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
        await profiles.delete_one(profile)

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('Profile Has Been Deleted.'),
            accent_color=discord.Color.green()
        )
        view.add_item(container)
        await interaction.edit_original_response(view=view)
        view.stop()

class ManageProfileOptions(ui.ActionRow):
    def __init__(self, bot: commands.Bot, moderator: discord.Member, inacted_user: discord.Member, profile: dict, select_options: list):
        super().__init__()
        self.bot = bot
        self.moderator = moderator
        self.inacted_user = inacted_user
        self.profile = profile
        self.select_options = select_options

        self.main_select = ui.Select(
            placeholder="What do you want to manage?",
            options = self.select_options,
            min_values=1,
            max_values=1
        )

        self.main_select.callback = self.main_select_callback

        self.add_item(self.main_select)
    
    async def main_select_callback(self, interaction: discord.Interaction):
        interaction_check(self.moderator, interaction.user)

        if self.main_select.values[0] == "edit_profile":
            await edit_profile(self.bot, interaction, self.moderator, self.inacted_user, self.profile)
        elif self.main_select.values[0] == "manage_units":
            await manage_units(self.bot, interaction, self.moderator, self.inacted_user, self.profile)
        elif self.main_select.values[0] == "view_requests":
            await view_requests(self.bot, interaction, self.moderator, self.inacted_user, self.profile)
        elif self.main_select.values[0] == "delete_profile":
            await delete_profile(self.bot, interaction, self.moderator, self.inacted_user, self.profile)

class ManageProfileMainView(ui.LayoutView):
    def __init__(self, bot: commands.Bot, moderator: discord.Member, inacted_user: discord.Member, profile: dict, dept_options: dict, is_owner=False):
        super().__init__(timeout=300)

        private_unit = ", ".join(profile.get('private_unit', []))

        if (
            any(role.id in (1428178727824658502, 1450297796174286900) for role in moderator.roles)
            and not any(role.id in (1422416268585341049, 1413208971304636597, 1450297609515307134, 1450297617073442816) for role in moderator.roles)
            and not is_owner
        ):
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
           container = ui.Container(
                ui.TextDisplay('## Manage Profile'),
                ui.Separator(),
                ui.TextDisplay('### Profile Information'),
                ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}"),
                ui.Separator(),
                ManageProfileOptions(bot, moderator, inacted_user, profile, select_options),
                accent_color=discord.Color.light_grey()
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
               discord.SelectOption(
                   label = "Delete Profile",
                   value = "delete_profile",
                   description = "Delete the profile",
                   emoji="<:Delete_Profile_Blackstar:1499178664913272832>"
               ),
           ]
            container = ui.Container(
                ui.TextDisplay('## Manage Profile'),
                DepartmentSelect(bot, moderator, inacted_user, profile, dept_options),
                ui.Separator(),
                ui.TextDisplay('### Profile Information'),
                ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}"),
                ui.Separator(),
                ManageProfileOptions(bot, moderator, inacted_user, profile, select_options),
                accent_color=discord.Color.light_grey()
            )


        self.add_item(container)

