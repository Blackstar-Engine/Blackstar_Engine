import discord
from discord import ui
import random
from utils.constants import economy_profiles

class MineButton(ui.Button):
    def __init__(self, row, col, index, currency):
        super().__init__(label="?", style=discord.ButtonStyle.blurple)
        self.row = row
        self.col = col
        self.index = index
        self.currency = currency

    async def callback(self, interaction: discord.Interaction):
        view: Minesweeper = self.view

        if interaction.user.id != view.user.id:
            return await interaction.response.send_message(
                "You do not have permission to interact with this game!",
                ephemeral=True
            )

        if self.index in view.mine_positions:
            self.label = "💣"
            self.style = discord.ButtonStyle.red
            
            view.lost = True
            self.disabled = True
            view.update_payout()
            view.buttons.remove(self)
            view.end_game()
            view.container.accent_color = discord.Color.red() 

            await economy_profiles.update_one(
                {
                    "user_id":interaction.user.id,
                },
                {
                    "$inc":{"currency":-self.currency}
                }
            )      

        else:
            self.label = "✔"
            self.style = discord.ButtonStyle.green
            view.buttons.remove(self)
            view.revealed += 1
            view.update_payout()
        self.disabled = True

        await interaction.response.edit_message(view=view)

class Minesweeper(ui.LayoutView):
    def __init__(self, user, currency):
        super().__init__(timeout=None)

        self.user = user
        self.currency = currency
        self.mines = 5
        self.buttons = []
        self.game = True
        self.lost = False

        self.revealed = 0
        self.tile_value = 0.12 + (self.mines * 0.01)
        self.mine_positions = set(random.sample(range(20), self.mines))
        self.earnings = ui.TextDisplay("Current Earnings: 1.00x (+0✦)")

        self.container = ui.Container(
            ui.TextDisplay("### Minesweeper"),
            ui.Separator(),
            self.earnings
        )
        self.container.accent_color = discord.Color.light_gray()

        for row in range(5):
            row_buttons = []

            for col in range(4):
                index = row * 4 + col
                button = MineButton(row, col, index, self.currency)
                self.buttons.append(button)
                row_buttons.append(button)

            action_row = ui.ActionRow(*row_buttons)
            self.container.add_item(action_row)
        self.add_item(self.container)
    
        self.cash_out = ui.Button(label="Cash Out", style=discord.ButtonStyle.success)
        self.cash_out.callback = self.cash_out_callback

        action_row = ui.ActionRow(self.cash_out)
        self.container.add_item(ui.Separator())
        self.container.add_item(action_row)

    
    def update_payout(self):
        if self.lost == True:
            self.earnings.content = (f"Current Earnings 0.00x (-{self.currency}✦)")
            return
        multiplier = 1 + (self.revealed * self.tile_value)
        payout = int(self.currency * multiplier)
        gain = payout - self.currency 

        self.earnings.content = (
            f"Current Earnings: {multiplier:.2f}x (+{gain}✦)"
        )

    async def cash_out_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You do not have permisson to interact with this game!", ephemeral=True)
        
        multiplier = 1 + (self.revealed * self.tile_value)
        payout = int(self.currency * multiplier)    

        self.container.accent_color = discord.Color.green()
        self.cash_out.disabled = True
        self.end_game()

        multiplier = 1 + (self.revealed * self.tile_value)
        payout = int(self.currency * multiplier)
        gain = payout - self.currency 

        await economy_profiles.update_one(
            {
                "user_id":interaction.user.id,
            },
            {
                "$inc":{"currency":+gain}
            }
        )      
        await interaction.response.edit_message(view=self)

    def end_game(self):
        self.game = False 
        for button in self.buttons:
            if button.index in self.mine_positions:
                button.label = "💣"
                button.style = discord.ButtonStyle.grey
            else:
                button.label = "✔"
                button.style = discord.ButtonStyle.grey

            button.disabled = True
        self.cash_out.disabled = True

