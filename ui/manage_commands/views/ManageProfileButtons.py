import discord
from utils.constants import profiles, departments
from ui.manage_commands.modals.EditProfile import EditProfileModal
from ui.manage_commands.views.ConfirmRemoval import ConfirmRemovalView
from ui.manage_commands.views.ProfileManageUnits import ProfileManageUnitsView
from ui.manage_commands.views.DepartmentButtons import DepartmentButtons
from ui.manage_commands.views.AdminTools import ManageDepartmentRow
from utils.utils import interaction_check, fetch_unit_options, has_approval_perms, fetch_id
from discord import ui, Interaction
import asyncio

class SelectAction(ui.ActionRow):
    def __init__(self, bot, user, options, profile):
        super().__init__()
        self.profile = profile
        self.bot = bot
        self.user = user

        self.role_select = ui.Select(
            placeholder="Select a Role",
            min_values=1,
            max_values=1,
            options=options
        )

        self.role_select.callback = self.dept_role_select

        self.add_item(self.role_select)

    async def dept_role_select(self, interaction: discord.Interaction):
        value = self.role_select.values[0]

        self.role_select.values.clear()

        options = fetch_unit_options(self.profile)
        is_owner = await self.bot.is_owner(interaction.user)
        view = ManageProfileButtons(self.bot, interaction, interaction.user, self.profile, options, is_owner=is_owner)

        await interaction.response.edit_message(view=view)

        if value == "no_units":
            return
        
        department = self.profile["unit"][value]

        view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {value} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(self.bot, self.user, value, self.profile),
            accent_color=discord.Color.light_grey()
        )

        if (
            is_owner
            or await has_approval_perms(self.user, 6)
        ):
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.profile, value))

        view.add_item(container)

        await interaction.followup.send(view=view, ephemeral=True)

class ButtonsAction1(ui.ActionRow):
    def __init__(self, bot, user, profile):
        super().__init__()
        self.bot = bot
        self.profile = profile
        self.user = user

        edit_button = ui.Button(label="Edit", style=discord.ButtonStyle.gray, row=1)
        manage_units_button = ui.Button(label="Manage Units", style=discord.ButtonStyle.gray, row=1)

        edit_button.callback = self.manage_profile_edit
        manage_units_button.callback = self.manage_profile_units

        self.add_item(edit_button)
        self.add_item(manage_units_button)
    
    async def manage_profile_edit(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)

        modal = EditProfileModal(self.bot, self.profile)
        await interaction.response.send_modal(modal)
        await modal.wait()

        roblox_name = modal.roblox_name.value
        timezone = modal.timezone.value
        codename = modal.codename.value
        status = modal.status.value

        self.profile["roblox_name"] = roblox_name
        self.profile["timezone"] = timezone
        self.profile["codename"] = codename
        self.profile["status"] = status.title()

        options = fetch_unit_options(self.profile)
        is_owner = await self.bot.is_owner(interaction.user)
        view = ManageProfileButtons(
            self.bot,
            interaction,
            self.user,
            self.profile,
            options,
            is_owner=is_owner
        )

        await interaction.edit_original_response(view=view)
    
    async def manage_profile_units(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)

        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        results = await departments.find().to_list(length=None)

        user_units = []
        units = dict(self.profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                user_units.append(unit)

        user_private_units = set(self.profile.get("private_unit", []))

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

        view = ProfileManageUnitsView(self.bot, self.user, self.profile, normal_unit_results, private_unit_results)

        await interaction.response.edit_message(view=view)
        await view.wait()

        # 🔄 Reload profile after submit
        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        options = fetch_unit_options(self.profile)
        is_owner = await self.bot.is_owner(interaction.user)
        manage_profile_view = ManageProfileButtons(
            self.bot,
            interaction,
            self.user,
            self.profile,
            options,
            is_owner=is_owner
        )

        await interaction.edit_original_response(view=manage_profile_view)

class ButtonsAction2(ui.ActionRow):
    def __init__(self, bot, user, profile):
        super().__init__()
        self.bot = bot
        self.profile = profile
        self.user = user

        delete_button = ui.Button(label="Delete", style=discord.ButtonStyle.red, row=1)

        delete_button.callback = self.manage_profile_delete

        self.add_item(delete_button)
    
    async def manage_profile_delete(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)

        confirm_buttons = ConfirmRemovalView(self.bot, self.user, self.profile, 0)
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
            await profiles.delete_one(self.profile)

            view = ui.LayoutView()
            container = ui.Container(
                ui.TextDisplay('Profile Has Been Deleted.'),
                accent_color=discord.Color.green()
            )
            view.add_item(container)
            await interaction.edit_original_response(view=view)
            view.stop()

class ManageProfileButtons(ui.LayoutView):
    def __init__(self, bot, ctx, user, profile, options, is_owner=False):
        super().__init__(timeout=300)

        if isinstance(ctx, discord.Interaction):
            author = ctx.user
        else:
            author = ctx.author

        private_unit = ", ".join(profile.get('private_unit', []))

        if (
            any(role.id == 1428178727824658502 for role in author.roles)
            and not any(role.id in {1422416268585341049, 1413208971304636597} for role in author.roles)
            and not is_owner
        ):
           container = ui.Container(
                ui.TextDisplay('## Manage Profile'),
                ui.Separator(),
                ui.TextDisplay('### Profile Information'),
                ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}"),
                ui.Separator(),
                ButtonsAction1(bot, user, profile),
                accent_color=discord.Color.light_grey()
            )
        else:
            container = ui.Container(
                ui.TextDisplay('## Manage Profile'),
                SelectAction(bot, user, options, profile),
                ui.Separator(),
                ui.TextDisplay('### Profile Information'),
                ui.TextDisplay(f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}"),
                ui.Separator(),
                ButtonsAction1(bot, user, profile),
                ui.Separator(),
                ButtonsAction2(bot, user, profile),
                accent_color=discord.Color.light_grey()
            )


        self.add_item(container)

