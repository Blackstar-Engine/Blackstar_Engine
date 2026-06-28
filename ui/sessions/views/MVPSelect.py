import discord

class MVPSelect(discord.ui.UserSelect):
    def __init__(self, parent_view):
        super().__init__(
            custom_id="mvp_user_select",
            placeholder="Select all MVPs",
            min_values=1,
            max_values=10
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.mvps = [user.id for user in self.values]

        await interaction.response.defer()

        self.parent_view.stop()


class MVPSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.mvps = []
        self.add_item(MVPSelect(self))