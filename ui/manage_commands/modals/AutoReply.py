import discord
from utils.constants import auto_replys

class AutoReplyAddModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Add New Record")
        self.bot = bot
        self.data = None

        self.message = discord.ui.TextInput(
            label="Message",
            placeholder="Hello",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.message)

        self.response = discord.ui.TextInput(
            label="Response",
            placeholder="Welcome to the server!", 
            required=True,
            row=2,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.response)
    
    async def on_submit(self, interaction: discord.Interaction):
        message = self.message.value
        response = self.response.value
        
        self.data = {
            "guild_id": interaction.guild.id,
            "message": message,
            "response": response,
            "created_by": interaction.user.id
        }

        await auto_replys.insert_one(self.data)

        embed = discord.Embed(
            title="New Auto Reply Added",
            description=f"**Message:** {message}\n"
                       f"**Response:** {response}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)