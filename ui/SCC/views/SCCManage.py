import discord
from discord import ui
from utils.constants import combat_profiles


class CombatCategories(ui.Select):
    def __init__(self, view):
        self.v = view
        options = [
            discord.SelectOption(label="Short Range", value="short_range"),
            discord.SelectOption(label="Long Range", value="long_range"),
            discord.SelectOption(label="Teamwork & Coordination", value="teamwork"),
            discord.SelectOption(label="Leadership", value="leadership"),
            discord.SelectOption(label="Game Sense", value="gamesense"),
            discord.SelectOption(label="Movement", value="movement")
        ]

        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.category = self.values[0]
        await interaction.response.defer()

class CombatRankings(ui.Select):
    def __init__(self, view, documents):
        self.v = view
        options = []
        for doc in documents:
            options.append(discord.SelectOption(label=doc["rank"]))

        super().__init__(
            placeholder="Choose a ranking...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.rank = self.values[0]
        await interaction.response.defer()

class CombatMain(ui.LayoutView):
    def __init__(self, documents, user):
        super().__init__()

        self.category = None
        self.rank = None
        self.user = user

        submit_button = ui.Button(label="Submit", style=discord.ButtonStyle.green)

        async def submit_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            await combat_profiles.update_one(
                {"user_id": self.user.id},
                {
                    "$set": {
                        self.category:self.rank
                    }
                },
                upsert=True
            )

            await interaction.followup.send(f"Updated SCC Ranking to **{self.rank}**", ephemeral=True)

        submit_button.callback = submit_callback

        container = ui.Container(
            ui.TextDisplay("### SCC Selection"),
            ui.TextDisplay("Please select a category and rank you want this user to be."),
            ui.ActionRow(CombatCategories(self)),
            ui.ActionRow(CombatRankings(self, documents)),
            ui.Separator(),
            ui.ActionRow(submit_button)
        )

        self.add_item(container)
