import discord
from discord.ext import commands
from discord.ui import View, Button, Modal
from utils.utils import interaction_check

class PaginatorView(View):
    def __init__(self, bot, user, items):
        super().__init__()
        self.bot = bot
        self.user = user
        self.items = items
        self.current_index = 0
        self.extra_buttons = []

        for button in self.extra_buttons:
            self.add_item(button)
        
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        prev_button = Button(
            label="Previous",
            style=discord.ButtonStyle.gray,
            disabled=self.current_index <= 0,
            row=1
        )
        prev_button.callback = self.previous_record
        self.add_item(prev_button)

        next_button = Button(
            label="Next",
            style=discord.ButtonStyle.grey,
            disabled=self.current_index >= len(self.items) - 1,
            row=1
        )
        next_button.callback = self.next_record
        self.add_item(next_button)

        for button in self.extra_buttons:
            self.add_item(button)

    def create_record_embed(self):
        if not self.items or self.current_index >= len(self.items):
            return discord.Embed(
                title="No Records Found",
                description="No records available to display.",
                color=discord.Color.light_grey()
            )
        
        record = self.items[self.current_index]

        embed = discord.Embed(
            title=f"Record #{self.current_index + 1}",
            description="",
            color=discord.Color.light_grey()
        )

        for key, value in record.items():
            if key not in ["message_id", "user_id", "channel_id", "guild_id", "created_at", "content", "attachments", "mentions", "reactions", "_id"]:
                if isinstance(value, int):
                    embed.add_field(name=key.title(), value=f"<@{value}>", inline=False)
                else:
                    embed.add_field(name=key.title(), value=value, inline=False)

        embed.set_footer(text=f"Record {self.current_index + 1} of {len(self.items)}")
        
        return embed

    async def previous_record(self, interaction: discord.Interaction):
        await interaction_check(self.user, interaction.user)
        
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            embed = self.create_record_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def next_record(self, interaction: discord.Interaction):
        await interaction_check(self.user, interaction.user)
        
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.update_buttons()
            embed = self.create_record_embed()
            await interaction.response.edit_message(embed=embed, view=self)