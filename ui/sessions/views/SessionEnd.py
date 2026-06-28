import discord
from discord.ext import commands
from ui.CustomModal import CustomModal

class EnterModal(discord.ui.View):
    def __init__(self, bot, session):
        super().__init__()
        self.bot = bot
        self.session = session 
        self.deployment_type = None
    
    @discord.ui.button(label="Click to Enter", style=discord.ButtonStyle.grey)
    async def enter_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CustomModal(
            "Session Ending",
            [
                (
                    "deploy_type",
                    discord.ui.TextInput(
                        label="Deployment Type",
                        placeholder="Training",
                        required=True,
                        max_length=500,
                    )
                )
            ]
        )

        await interaction.response.send_modal(modal)

        await modal.wait()

        self.deployment_type = modal.deploy_type.value

        self.stop()

