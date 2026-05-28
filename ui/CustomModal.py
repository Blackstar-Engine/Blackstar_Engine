import discord
from discord.ui import Modal

class CustomModal(Modal, title="Edit Reason"):
    def __init__(self, title, options, args: dict = None, callback=None):
        super().__init__(title=title)
        if args is None:
            args = {}
        self.saved_items = {}
        self.args = args
        self._custom_callback = callback
        self.interaction = None

        for name, option in options:
            self.add_item(option)
            self.saved_items[name] = option

    async def on_submit(self, interaction: discord.Interaction):
        for key, item in self.saved_items.items():
            setattr(self, key, item)
        self.interaction = interaction
        await interaction.response.defer(**self.args)
        
        if self._custom_callback:
            await self._custom_callback(self, interaction)

        self.stop()