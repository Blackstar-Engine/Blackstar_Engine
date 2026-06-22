import discord
from discord.ui import View, Button
from utils.utils import interaction_check
from datetime import datetime

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
                color=discord.Color.light_grey(),
            )

        record = self.items[self.current_index]

        embed = discord.Embed(
            title=f"Record #{self.current_index + 1}",
            description="",
            color=discord.Color.light_grey(),
        )

        excluded = {
            "message_id",
            "channel_id",
            "guild_id",
            "created_at",
            "content",
            "attachments",
            "mentions",
            "reactions",
            "_id",
        }

        for key, value in record.items():
            if key in excluded:
                continue

            name = self._display_key(key)
            val = self._format_value(key, value)
            embed.add_field(name=name, value=val, inline=True)

        embed.set_footer(text=f"Record {self.current_index + 1} of {len(self.items)}")
        return embed

    def _display_key(self, k: str) -> str:
        k = k.replace("_id", "")
        k = k.replace("_", " ")
        return k.title()

    def _format_value(self, key: str, value):
        if isinstance(value, int):
            return self._format_int(key, value)
        if isinstance(value, list):
            return self._format_list(value)
        if isinstance(value, datetime):
            try:
                return discord.utils.format_dt(value)
            except Exception:
                return str(value)
        if isinstance(value, dict):
            return self._format_dict(value)
        return str(value)

    def _format_int(self, k: str, v: int):
        lk = k.lower()
        if "timestamp" in lk:
            return f"<t:{v}:R>"
        if any(x in lk for x in ("id", "user", "moderator")):
            return f"<@{v}>"
        return str(v)

    def _format_list(self, v: list):
        parts = []
        for item in v:
            if isinstance(item, int):
                parts.append(f"<@{item}>")
            else:
                parts.append(str(item))
        return ", ".join(parts)

    def _format_dict(self, d: dict):
        parts = []
        for k, val in d.items():
            if isinstance(val, dict):
                sub = [f"**{sk}**: {sv}" for sk, sv in val.items()]
                parts.append(f"__**{k}**__ -\n" + "\n".join(sub))
            else:
                parts.append(f"**{k}**: {val}")
        return "\n".join(parts)

    async def previous_record(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        
        if self.current_index > 0:
            self.current_index -= 1
            self.update_buttons()
            embed = self.create_record_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    async def next_record(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        
        if self.current_index < len(self.items) - 1:
            self.current_index += 1
            self.update_buttons()
            embed = self.create_record_embed()
            await interaction.response.edit_message(embed=embed, view=self)