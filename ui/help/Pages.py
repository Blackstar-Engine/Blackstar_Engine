import discord
from discord.ui import View, Button

commands = [
  "> `!help` - This command\n",
  "> `!execute @User` - Timeout for 10 seconds **(Wolf Only)**\n",
  "> `!embed text` - Custom Embed **(Wolf Only)**\n",
  "> `!join #channel` - Add bot to VC to enable TTS\n",
  "> `!leave` - Remove bot from VC to disable TTS\n",
  "> `!send-reactions` - Send Reaction Roles **(Foundation Only)**\n",
  "> `!promotion request department proof` - Send a promotion request\n",
  "> `!profile` - View your profile\n",
  "> `!points request <amount> proof` - Send a points request\n",
  "> `!manage auto_reply` - Manage all server auto replies **(Foundation & Site Command)**\n",
  "> `!manage profile` - Manage a user’s profile **(Foundation & Site Command)**\n",
  "> `!loa request time reason` - Send an LOA request\n",
  "> `!loa manage @User` - Manage your own or another user’s LOA\n",
  "> `!loa active` - See all active LOAs **(Foundation & Site Command)**\n",
  "> `!enlistment request` - Request to join a department\n",
  "> `!roleuser @User department` - Give user the overall and first rank for that department.\n",
  "> `!dm_punish @User text` - Notifies a user that disciplinary action has been taken against them **(Junior Mod+ and Central Command+)**\n",
  "> `!say <text>` - Makes the bot say a message of your choosing **(Wolf only)**\n",
  "> `!send_votes game_link` - Pings everyone who reacted with a checkmark to a training **(Central Command+)**\n",
  "> `!move #channel` - Move the bot to a different VC **(Central Command+)**\n",
]

class Pages(View):
    def __init__(self, chunk_size: int = 6) -> None:
        super().__init__(timeout=None)
        self.chunk_size = chunk_size
        self.pages = [commands[i : i + chunk_size] for i in range(0, len(commands), chunk_size)]
        self.current = 0
        self.embed = discord.Embed(
            title="Command List",
            description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "\n".join(self.pages[self.current]),
            color=discord.Color.light_gray()
        )
        self.embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        self.update_buttons()

    def update_buttons(self):
        self.previous.disabled = self.current == 0
        self.next.disabled = self.current == len(self.pages) - 1

    @discord.ui.button(label="←", style=discord.ButtonStyle.grey)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current > 0:
            self.current -= 1
            self.embed.description = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "\n".join(self.pages[self.current])
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embed, view=self)

    @discord.ui.button(label="→", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.current < len(self.pages) - 1:
            self.current += 1
            self.embed.description = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "\n".join(self.pages[self.current])
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embed, view=self)

    