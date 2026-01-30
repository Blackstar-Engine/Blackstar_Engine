import discord
from utils.constants import profiles

class DemoteRankView(discord.ui.View):
    def __init__(self, profile, unit, ranks, current_rank):
        super().__init__(timeout=120)

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

        self.rank_select.options = options

    @discord.ui.select(placeholder="Select rank to demote to", options=[])
    async def rank_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        new_rank = select.values[0]

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                f"unit.{self.unit}.rank": new_rank
            }}
        )

        await interaction.response.send_message(
            f"✅ {self.unit} rank updated to **{new_rank}**",
            ephemeral=True
        )