import discord
from discord import ui
import random
import asyncio
from utils.constants import economy_profiles


class Slots(ui.LayoutView):
    def __init__(self, currency):
        super().__init__(timeout=120)

        self.currency = currency
        self.symbols = ["🍇", "🍌", "🍎", "🍒"]
        result = random.sample(self.symbols, 3)
        self.slots = ui.TextDisplay("*" + " ┃ ".join(result) + "*")
        self.status = ui.TextDisplay("Select the spin button to roll the slots!")
        self.duration = 5

        self.spin_button = ui.Button(label="Spin!", style=discord.ButtonStyle.green)
        self.spin_button.callback = self.spin_callback

        self.container = ui.Container(
            ui.TextDisplay("### Slots"),
            ui.Separator(),
            self.status,
            self.slots,
            ui.Separator(),
            ui.ActionRow(self.spin_button)
        )
        self.container.accent_color = discord.Color.light_gray()

        self.add_item(self.container)

    async def spin_callback(self, interaction: discord.Interaction):
        self.spin_button.disabled = True
        await interaction.response.defer()
        self.status.content = "Spinning the slots!"
        intervals = self.duration / 8
        for i in range(8):
            result = random.sample(self.symbols, 3)
            self.slots.content = "*" + " ┃ ".join(result) + "*"
            await interaction.edit_original_response(view=self)
            await asyncio.sleep(intervals)
        roll = random.random()
        symbols = self.symbols

        result = []

        if roll < 0.6:
            result = random.sample(self.symbols, 3)
            self.status.content = f"You have rolled nothing (-{self.currency}✦)"
            winnings = -self.currency
            self.container.accent_color = discord.Color.red()

        elif roll < 0.8:
            s = random.choice(symbols)
            other = random.choice([x for x in self.symbols if x != s])

            result = [s, s, other]
            random.shuffle(result)
            winnings = self.currency
            self.status.content = f"You have rolled two of a kind! (+{winnings}✦)"
            self.container.accent_color = discord.Color.green()

        else:
            s = random.choice(self.symbols)
            result = [s, s, s]
            winnings = 1.5*self.currency
            self.status.content = f"You have rolled three of a kind! (+{winnings}✦)"
            self.container.accent_color = discord.Color.green()

        self.slots.content = "*" + " ┃ ".join(result) + "*"
        await interaction.edit_original_response(view=self)

        await economy_profiles.update_one(
            {"user_id": interaction.user.id},
            {"$inc": {"currency": -winnings}}
        )
        return        