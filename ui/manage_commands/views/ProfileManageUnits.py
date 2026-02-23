import discord
from utils.constants import profiles, departments
from utils.utils import interaction_check
from discord import ui


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

        self.normal_units = []

        self.normal_units_select.callback = self.profile_manage_units
        self.add_item(self.normal_units_select)
    
    async def profile_manage_units(self, interaction: discord.Interaction):
        self.normal_units = self.normal_units_select.values
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

        self.private_units = []

        self.private_units_select.callback = self.profile_manage_private_units
        self.add_item(self.private_units_select)
    
    async def profile_manage_private_units(self, interaction: discord.Interaction):
        self.private_units = self.private_units_select.values
        await interaction.response.defer(ephemeral=True)

class SubmitButtonRow(ui.ActionRow):
    def __init__(self, profile, normal_row, private_row):
        super().__init__()
        self.profile = profile
        self.normal_row = normal_row
        self.private_row = private_row

        submit_button = ui.Button(
            label="Submit",
            style=discord.ButtonStyle.green
        )

        submit_button.callback = self.profile_manage_units_submit
        self.add_item(submit_button)

    async def profile_manage_units_submit(self, interaction: discord.Interaction):

        # ───── GET SELECTED VALUES DIRECTLY FROM ROWS ─────
        selected_units = set(self.normal_row.normal_units or [])
        selected_private_units = set(self.private_row.private_units or [])

        # ───── LOAD ALL NON-PRIVATE DEPARTMENTS ─────
        all_departments = await departments.find(
            {"is_private": False}
        ).to_list(length=None)

        dept_map = {d["display_name"]: d for d in all_departments}

        # Copy existing units safely
        units = dict(self.profile.get("unit", {}))

        # ───── ACTIVATE / ADD SELECTED NORMAL UNITS ─────
        for unit in selected_units:
            dept = dept_map.get(unit)
            if not dept:
                continue

            first_rank = (
                dept["ranks"][0]["name"]
                if dept.get("ranks")
                else None
            )

            unit_data = units.setdefault(unit, {})
            ensure_unit_defaults(unit_data, first_rank)
            unit_data["is_active"] = True

        # ───── DISABLE UNSELECTED NORMAL UNITS (NEVER DELETE) ─────
        for unit_name, unit_data in units.items():
            if unit_name not in selected_units:
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
        active_units = [
            unit_name
            for unit_name, unit_data in units.items()
            if unit_data.get("is_active")
        ]

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('### Units Updated'),
            ui.TextDisplay(f"**Units:** {', '.join(active_units) or 'None'}\n"),
            ui.TextDisplay(f"**Private Units:** {', '.join(selected_private_units) or 'None'}"),
            accent_color=discord.Color.green()
        )
        view.add_item(container)

        await interaction.response.edit_message(view=view)
        view.stop()
        self.view.stop()
class ProfileManageUnitsView(ui.LayoutView):
    def __init__(self, bot, profile, normal_units, private_units):
        super().__init__()

        self.bot = bot
        self.profile = profile

        self.normal_units_select = NormalUnitsRow(normal_units)
        self.private_units_select = PrivateUnitsRow(private_units)
        self.submit_button = SubmitButtonRow(
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