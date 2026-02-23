import discord
from utils.constants import profiles

class DemoteRankView(discord.ui.ActionRow):
    def __init__(self, profile, unit, ranks, current_rank):
        super().__init__()

        self.profile = profile
        self.unit = unit

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

        self.rank_select = discord.ui.Select(
            placeholder="Select rank to demote to",
            options=options,
            min_values=1,
            max_values=1
        )
        self.rank_select.callback = self.rank_select_callback
        self.add_item(self.rank_select)

    async def rank_select_callback(self, interaction: discord.Interaction):
        new_rank = self.rank_select.values[0]

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                f"unit.{self.unit}.rank": new_rank
            }}
        )
        
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(f"✅ {self.unit} rank updated to **{new_rank}**"),
            accent_color=discord.Color.green()
        )
        view.add_item(container)
        await interaction.response.edit_message(view=view)