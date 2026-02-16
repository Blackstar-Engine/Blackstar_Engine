import discord
from utils.constants import profiles, departments
from utils.utils import interaction_check


def ensure_unit_defaults(unit_data: dict, first_rank: str | None):
    """
    Initialize unit fields safely without overwriting existing data.
    """
    unit_data.setdefault("rank", first_rank)
    unit_data.setdefault("is_active", True)
    unit_data.setdefault("current_points", 0)
    unit_data.setdefault("total_points", 0)


class ProfileManageUnitsView(discord.ui.View):
    def __init__(self, bot, profile, user, normal_units, private_units):
        super().__init__(timeout=300)

        self.bot = bot
        self.profile = profile
        self.user = user

        # Track interaction state (critical for empty selections)
        self.normal_units_interacted = False
        self.private_units_interacted = False

        # Normal units select
        self.profile_manage_units.options = normal_units
        self.profile_manage_units.max_values = len(normal_units)
        self.profile_manage_units.min_values = 0

        # Private units select
        self.profile_manage_private_units.options = private_units
        self.profile_manage_private_units.max_values = len(private_units)
        self.profile_manage_private_units.min_values = 0

    # ───────────────────────── NORMAL UNITS ─────────────────────────

    @discord.ui.select(placeholder="No Units Selected", options=[])
    async def profile_manage_units(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):
        interaction_check(self.user, interaction.user)
        self.normal_units_interacted = True
        await interaction.response.defer(ephemeral=True)

    # ───────────────────────── PRIVATE UNITS ─────────────────────────

    @discord.ui.select(placeholder="No Private Units Selected", options=[])
    async def profile_manage_private_units(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select
    ):
        interaction_check(self.user, interaction.user)
        self.private_units_interacted = True
        await interaction.response.defer(ephemeral=True)

    # ───────────────────────── SUBMIT BUTTON ─────────────────────────

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def profile_manage_units_submit(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        interaction_check(self.user, interaction.user)

        # ───── NORMAL UNITS SELECTION ─────

        if self.normal_units_interacted:
            selected_units = set(self.profile_manage_units.values)
        else:
            selected_units = {
                opt.label
                for opt in self.profile_manage_units.options
                if opt.default
            }

        # ───── PRIVATE UNITS SELECTION ─────

        if self.private_units_interacted:
            selected_private_units = set(self.profile_manage_private_units.values)
        else:
            selected_private_units = {
                opt.label
                for opt in self.profile_manage_private_units.options
                if opt.default
            }

        # ───── LOAD NON-PRIVATE DEPARTMENTS ─────

        all_departments = await departments.find(
            {"is_private": False}
        ).to_list(length=None)

        dept_map = {d["display_name"]: d for d in all_departments}

        # Existing unit data (copy to mutate safely)
        units = dict(self.profile.get("unit", {}))

        # ───── ACTIVATE / ADD SELECTED UNITS ─────

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

        # ───── DEACTIVATE UNSELECTED UNITS (DO NOT DELETE) ─────

        for unit_name, unit_data in units.items():
            if unit_name not in selected_units:
                unit_data["is_active"] = False

        # ───── SAVE PROFILE ─────

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {
                "$set": {
                    "unit": units,
                    "private_unit": list(selected_private_units)
                }
            }
        )

        # ───── RESPONSE EMBED ─────

        active_units = [
            unit_name
            for unit_name, unit_data in units.items()
            if unit_data.get("is_active")
        ]

        embed = discord.Embed(
            title="Profile Units Updated",
            description=(
                f"**Units:** {', '.join(active_units) or 'None'}\n"
                f"**Private Units:** {', '.join(selected_private_units) or 'None'}"
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

        self.stop()
