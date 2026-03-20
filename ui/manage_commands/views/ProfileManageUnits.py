import discord
from utils.constants import profiles, departments
from discord import ui
from utils.utils import log_action

def ensure_unit_defaults(unit_data: dict, first_rank: str | None):
    """
    Initialize unit fields safely without overwriting existing data.
    """
    unit_data.setdefault("rank", first_rank)
    unit_data.setdefault("is_active", True)
    unit_data.setdefault("current_points", 0)
    unit_data.setdefault("total_points", 0)


class NormalUnitsRow(ui.ActionRow):
    def __init__(self, normal_units):
        super().__init__()

        self.normal_units_select = ui.Select(
            placeholder="No Units Selected",
            options=normal_units,
            min_values=0,
            max_values=len(normal_units)
        )

        self.selected_normal_units = None

        self.default_units = [opt.label for opt in normal_units if opt.default]

        self.normal_units_select.callback = self.profile_manage_units
        self.add_item(self.normal_units_select)
    
    async def profile_manage_units(self, interaction: discord.Interaction):
        self.selected_normal_units = self.normal_units_select.values
        await interaction.response.defer(ephemeral=True)

class PrivateUnitsRow(ui.ActionRow):
    def __init__(self, private_units):
        super().__init__()

        self.private_units_select = ui.Select(
            placeholder="No Private Units Selected",
            options=private_units,
            min_values=0,
            max_values=len(private_units)
        )

        self.selected_private_units = None

        self.default_units = [opt.label for opt in private_units if opt.default]

        self.private_units_select.callback = self.profile_manage_private_units
        self.add_item(self.private_units_select)
    
    async def profile_manage_private_units(self, interaction: discord.Interaction):
        self.selected_private_units = self.private_units_select.values
        await interaction.response.defer(ephemeral=True)

class SubmitButtonRow(ui.ActionRow):
    def __init__(self, bot, user, profile, normal_row_select, private_row_select):
        super().__init__()
        from ui.manage_commands.views.ReturnButton import ReturnButton
        self.profile = profile
        self.normal_row_select = normal_row_select
        self.private_row_select = private_row_select
        self.user = user

        submit_button = ui.Button(label="Submit", style=discord.ButtonStyle.green)

        submit_button.callback = self.profile_manage_units_submit

        self.add_item(submit_button)
        self.add_item(ReturnButton(bot, user))

    async def profile_manage_units_submit(self, interaction: discord.Interaction):

        # ───── GET SELECTED VALUES DIRECTLY FROM ROWS ─────
        if self.normal_row_select.selected_normal_units is None:
            selected_normal_units = self.normal_row_select.default_units
        else:
            selected_normal_units = self.normal_row_select.selected_normal_units
       
        if self.private_row_select.selected_private_units is None:
            selected_private_units = self.private_row_select.default_units
        else:
            selected_private_units = self.private_row_select.selected_private_units

        # ───── LOAD ALL NON-PRIVATE DEPARTMENTS ─────
        all_departments = await departments.find({"is_private": False}).to_list(length=None)

        dept_map = {dept["display_name"]: dept for dept in all_departments}

        # Copy existing units safely
        units = dict(self.profile.get("unit", {}))

        # ───── ACTIVATE / ADD SELECTED NORMAL UNITS ─────
        for unit in selected_normal_units:
            dept = dept_map.get(unit)
            if not dept:
                continue

            first_rank = dept["ranks"][0]["name"]

            unit_data = units.setdefault(unit, {})
            ensure_unit_defaults(unit_data, first_rank)
            unit_data["is_active"] = True

        # ───── DISABLE UNSELECTED NORMAL UNITS (NEVER DELETE) ─────
        for unit_name, unit_data in units.items():
            if unit_name not in selected_normal_units:
                unit_data["is_active"] = False

        # ───── SAVE PROFILE ─────
        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {
                "$set": {
                    "unit": units,  # always preserved
                    "private_unit": list(selected_private_units)  # add/remove freely
                }
            }
        )

        # ───── RESPONSE EMBED ─────
        active_units = [unit_name for unit_name, unit_data in units.items() if unit_data.get("is_active")]

        await log_action(ctx=interaction, log_type="department", user_id=self.user.id, department=', '.join(active_units) or 'None')

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('### Units Updated'),
            ui.TextDisplay(f"**Units:** {', '.join(active_units) or 'None'}\n"),
            ui.TextDisplay(f"**Private Units:** {', '.join(selected_private_units) or 'None'}"),
            accent_color=discord.Color.green()
        )
        view.add_item(container)

        await interaction.response.send_message(view=view, ephemeral=True)
        view.stop()
        self.view.stop()

class ProfileManageUnitsView(ui.LayoutView):
    def __init__(self, bot, user, profile, normal_units_results, private_units_results):
        super().__init__()
        self.bot = bot
        self.user = user
        self.profile = profile

        self.normal_units_select = NormalUnitsRow(normal_units_results)
        self.private_units_select = PrivateUnitsRow(private_units_results)

        self.submit_button = SubmitButtonRow(
            bot,
            user,
            profile,
            self.normal_units_select,
            self.private_units_select
        )

        container = ui.Container(
            ui.TextDisplay('## Units Selection'),
            ui.TextDisplay('Please select all units you want this user to be a part of.'),
            ui.Separator(),
            self.normal_units_select,
            self.private_units_select,
            ui.Separator(),
            self.submit_button,
        )

        self.add_item(container)