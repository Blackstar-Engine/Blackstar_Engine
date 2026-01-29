import discord

class RequestDenyModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Provide a Reason")
        self.bot = bot

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Because i said so!",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)