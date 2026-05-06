import discord
from discord import ui
import random
from utils.constants import economy_profiles

class MineButton(ui.Button):
    def __init__(self, index: int):
        super().__init__(label="?", style=discord.ButtonStyle.blurple)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: Minesweeper = self.view

        if interaction.user.id != view.user.id:
            return await interaction.response.send_message(
                "You do not have permission to interact with this game!",
                ephemeral=True
            )

        if view.game_over:
            return

        self.disabled = True

        # 💣 Hit a mine
        if self.index in view.mine_positions:
            self.label = "💣"
            self.style = discord.ButtonStyle.red

            view.game_over = True
            view.container.accent_color = discord.Color.red()

            await economy_profiles.update_one(
                {"user_id": interaction.user.id, "guild_id": interaction.guild.id},
                {"$inc": {"currency": -abs(view.bet)}}
            )

            view.update_payout()
            view.end_game()

        # ✅ Safe tile
        else:
            self.label = "✔"
            self.style = discord.ButtonStyle.green

            view.revealed.add(self.index)
            view.update_payout()

        await interaction.response.edit_message(view=view)


class Minesweeper(ui.LayoutView):
    def __init__(self, user, bet):
        super().__init__(timeout=None)

        self.user = user
        self.bet = bet
        self.mines = 5

        self.game_over = False
        self.revealed = set()

        self.tile_value = 0.12 + (self.mines * 0.01)
        self.mine_positions = set(random.sample(range(20), self.mines))

        self.earnings = ui.TextDisplay("Current Earnings: 1.00x (+0✦)")

        self.container = ui.Container(
            ui.TextDisplay("### Minesweeper"),
            ui.Separator(),
            self.earnings
        )
        self.container.accent_color = discord.Color.light_gray()

        # Create grid
        for row in range(5):
            row_buttons = []
            for col in range(4):
                index = row * 4 + col
                row_buttons.append(MineButton(index))

            self.container.add_item(ui.ActionRow(*row_buttons))

        self.add_item(self.container)

        # Cashout button
        self.cash_out = ui.Button(label="Cash Out", style=discord.ButtonStyle.success)
        self.cash_out.callback = self.cash_out_callback

        self.container.add_item(ui.Separator())
        self.container.add_item(ui.ActionRow(self.cash_out))

    # 🔢 Centralized multiplier logic
    def get_multiplier(self):
        return 1 + (len(self.revealed) * self.tile_value)

    def get_payout(self):
        return int(self.bet * self.get_multiplier())

    def update_payout(self):
        if self.game_over:
            self.earnings.content = f"Current Earnings: 0.00x (-{self.bet}✦)"
            return

        multiplier = self.get_multiplier()
        gain = self.get_payout() - self.bet

        self.earnings.content = f"Current Earnings: {multiplier:.2f}x (+{gain}✦)"

    async def cash_out_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You do not have permission to interact with this game!",
                ephemeral=True
            )

        if self.game_over:
            return

        self.game_over = True
        self.container.accent_color = discord.Color.green()
        self.cash_out.disabled = True

        gain = self.get_payout() - self.bet

        await economy_profiles.update_one(
            {"user_id": interaction.user.id, "guild_id": interaction.guild.id},
            {"$inc": {"currency": abs(gain)}}
        )

        self.end_game()
        await interaction.response.edit_message(view=self)

    def _reveal_unrevealed_mines(self, button: MineButton):
        if button.disabled and button.label in ("✔", "💣"):
            return False
        
        button.label = "💣" if button.index in self.mine_positions else "✔"
        button.style = discord.ButtonStyle.grey
        button.disabled = True
        return True

    def _reveal_all_buttons(self):
        container = next(
            (item for item in self.children if isinstance(item, ui.Container)),
            None
        )
        
        if not container:
            return
        
        for row in container.children:
            if not isinstance(row, ui.ActionRow):
                continue
            for button in row.children:
                if isinstance(button, MineButton):
                    self._reveal_unrevealed_mines(button)

    def end_game(self):
        self._reveal_all_buttons()
        self.cash_out.disabled = True