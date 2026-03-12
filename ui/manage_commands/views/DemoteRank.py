import discord
from utils.constants import profiles
from ui.manage_commands.views.DepartmentButtons import DepartmentButtons
from ui.manage_commands.views.AdminTools import ManageDepartmentRow
from discord import ui
from utils.utils import has_approval_perms

class DemoteRankView(ui.ActionRow):
    def __init__(self, bot, user, profile, unit, ranks, current_rank):
        super().__init__()

        self.profile = profile
        self.unit = unit
        self.bot = bot
        self.user = user

        # Find current rank order
        current_rank_obj = next(
            (r for r in ranks if r["name"] == current_rank),
            None
        )

        if not current_rank_obj:
            self.valid_ranks = []
        else:
            current_order = current_rank_obj["order"]
            self.valid_ranks = [
                r for r in ranks
                if r.get("order", 0) <= current_order
            ]

        options = [
            discord.SelectOption(label=r["name"])
            for r in self.valid_ranks
        ]

        self.rank_select = ui.Select(
            placeholder="Select rank to demote to",
            options=options,
            min_values=1,
            max_values=1
        )
        self.rank_select.callback = self.rank_select_callback
        self.add_item(self.rank_select)

    async def rank_select_callback(self, interaction: discord.Interaction):
        from ui.manage_commands.views.ManageProfileButtons import ManageProfileButtons
        new_rank = self.rank_select.values[0]

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                f"unit.{self.unit}.rank": new_rank
            }}
        )

        self.profile["unit"][self.unit]["rank"] = new_rank

        department = self.profile["unit"][self.unit]

        main_view = ui.LayoutView()

        container = ui.Container(
            ui.TextDisplay(f"## {self.unit} Information"),
            ui.TextDisplay(f"**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}"),
            ui.Separator(),
            DepartmentButtons(self.bot, self.user, self.unit, self.profile),
            accent_color=discord.Color.light_grey()
        )

        if (
            await self.bot.is_owner(interaction.user)
            or await has_approval_perms(self.user, 6)
        ):
            container.add_item(ui.Separator())
            container.add_item(ManageDepartmentRow(self.profile, self.unit))

        main_view.add_item(container)

        await interaction.response.edit_message(view = main_view)
        
        confirm_view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay(f"✅ {self.unit} rank updated to **{new_rank}**"),
            accent_color=discord.Color.green()
        )
        confirm_view.add_item(container)
        await interaction.followup.send(view=confirm_view, ephemeral=True)
