import discord
from discord.ext import commands
from discord import ui

class CreateEmbedModal(ui.Modal, title="Create DM Embed"):
    def __init__(self, bot: commands.Bot, punished_user: discord.Member):
        super().__init__()
        self.bot = bot
        self.punished_user = punished_user

        self.etitle = ui.TextInput(
            label = "Title",
            placeholder="DM Punishment",
            default = "Notice of Disciplinary Action",
            required=True, 
            style=discord.TextStyle.short,
            max_length=256
        )

        self.edescription = ui.TextInput(
            label = "Description",
            placeholder="You did a bad thing! You are now banned!",
            required=True, 
            style=discord.TextStyle.long,
            max_length=4000
            )
        
        self.add_item(self.etitle)
        self.add_item(self.edescription)
        
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.etitle.value,
            description=self.edescription.value,
            color=discord.Color.red()
        )
        await self.punished_user.send(embed=embed)
        await interaction.response.send_message(f"DM Embed sent to {self.punished_user.mention}.", ephemeral=True)