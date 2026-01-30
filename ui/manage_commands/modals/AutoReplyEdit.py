import discord
from utils.constants import auto_replys
from discord.ui import Modal

class AutoReplyEditModal(Modal):
    def __init__(self, bot, record):
        super().__init__(title="Edit Record")
        self.bot = bot
        self.record = record
        self.data = None

        self.message = discord.ui.TextInput(
            label="Message",
            default=record.get("message", ""),
            placeholder=record.get("message", ""),
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.message)

        self.response = discord.ui.TextInput(
            label="Response",
            default=record.get("response", ""),
            placeholder=record.get("response", ""),
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


        await auto_replys.update_one(self.record, {"$set": self.data})

        embed = discord.Embed(
            title="Record Updated",
            description=f"**Message:** {message}\n"
                       f"**Response:** {response}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()