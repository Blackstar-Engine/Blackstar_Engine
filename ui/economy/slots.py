import discord
from discord import ui
import random
import asyncio
from utils.constants import economy_profiles


class Slots(ui.LayoutView):
    def __init__(self, bet):
        super().__init__(timeout=120)

        # grab currency, cymbols, and duration for the spin
        self.bet = abs(int(bet))
        self.symbols = ["🍇", "🍌", "🍎", "🍒"]
        self.duration = 5

        # Create the spin button and its callback
        self.spin_button = ui.Button(label="Spin!", style=discord.ButtonStyle.green)
        self.spin_button.callback = self.spin_callback

        # Create a random slot result and set the slots and status
        # This needs to be in declared in self so you can edit it later in the callback
        result = random.choices(self.symbols, k=3)
        self.slots = ui.TextDisplay("*" + " ┃ ".join(result) + "*")
        self.status = ui.TextDisplay("Select the spin button to roll the slots!")

        # Create the container for the entire view and add it to the view
        self.container = ui.Container(
            ui.TextDisplay("### Slots"),
            ui.Separator(),
            self.status,
            self.slots,
            ui.Separator(),
            ui.ActionRow(self.spin_button),
            accent_color=discord.Color.light_grey()
        )
        self.add_item(self.container)
    
    def format_slots(self, result):
        return f"*{' ┃ '.join(result)}*"

    def roll_slots(self):
        roll = random.random()

        if roll < 0.6:
            result = random.sample(self.symbols, 3)
            winnings = -self.bet
            message = f"You have rolled nothing (-{self.bet}✦)"
            color = discord.Color.red()

        elif roll < 0.8:
            s = random.choice(self.symbols)
            other = random.choice([sym for sym in self.symbols if sym != s])

            result = [s, s, other]
            random.shuffle(result)

            winnings = self.bet
            message = f"You have rolled two of a kind! (+{winnings}✦)"
            color = discord.Color.green()

        else:
            s = random.choice(self.symbols)
            result = [s, s, s]

            winnings = max(2, int(1.5 * self.bet))
            message = f"You have rolled three of a kind! (+{winnings}✦)"
            color = discord.Color.green()

        return result, winnings, message, color

    async def spin_callback(self, interaction: discord.Interaction):
        if self.spin_button.disabled:
            await interaction.response.defer()
            return
        # disable the spin button and update the message to prevent multiple spins at once
        self.spin_button.disabled = True
        await interaction.response.edit_message(view=self)

        # disable the spin button and update the status
        self.status.content = "Spinning the slots!"
        await interaction.edit_original_response(view=self)

        # declare how many intervals it will spin
        steps = 8
        interval = self.duration / steps

        # random generate new slots every interval
        for _ in range(steps):
            result = random.sample(self.symbols, 3)
            self.slots.content = self.format_slots(result)
            await interaction.edit_original_response(view=self)
            await asyncio.sleep(interval)

        # determine a random roll
        result, winnings, message, color = self.roll_slots()

        self.status.content = message
        self.container.accent_color = color
        self.slots.content = self.format_slots(result)

        await interaction.edit_original_response(view=self)

        return await economy_profiles.update_one(
            {"user_id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$inc": {"currency": winnings}}
        )     