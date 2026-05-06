import discord
from discord import ui
import random

from utils.utils import check_eco_profile
from utils.constants import economy_profiles


class Blackjack(ui.LayoutView):
    def __init__(self, user, bet):
        super().__init__(timeout=None)

        self.user = user
        self.bet = bet

        self.emoji_dict = {
            0: "<:Unknown:1499985461106446448>",
            1: "<:AceSpades:1499248426590933032>",
            2: "<:TwoOfSpades:1499248497461956628>",
            3: "<:ThreeOfClubs:1499248412128972831>",
            4: "<:FourOfHearts:1499248413844181092>",
            5: "<:FiveOfDiamonds:1499248415035363410>",
            6: "<:SixOfHearts:1499248416629456906>",
            7: "<:SevenOfSpades:1499248418030223431>",
            8: "<:EightOfDiamonds:1499248419510685807>",
            9: "<:NineOfSpades:1499248421067030558>",
            10: "<:TenOfClubs:1499249778620633240>",
            11: "<:JackOfSpade:1499248422459539466>",
            12: "<:QueenOfClubs:1499248423717834915>",
            13: "<:KingofHearts:1499250100919205960>",
        }

        self.dealer_cards = [random.randint(1, 13), 0]
        self.player_cards = [random.randint(1, 13)]

        self.title = ui.TextDisplay("### Blackjack")
        self.dealer_display = ui.TextDisplay("")
        self.player_display = ui.TextDisplay("")

        self.hit_button = ui.Button(label="Hit", style=discord.ButtonStyle.danger)
        self.hit_button.callback = self.hit_callback

        self.stand_button = ui.Button(label="Stand", style=discord.ButtonStyle.success)
        self.stand_button.callback = self.stand_callback

        self.container = ui.Container(
            self.title,
            ui.Separator(),
            ui.TextDisplay("**Dealers Hand**"),
            self.dealer_display,
            ui.TextDisplay("**Players Hand**"),
            self.player_display,
            ui.Separator(),
            ui.ActionRow(self.hit_button, self.stand_button)
        )

        self.container.accent_color = discord.Color.light_gray()
        self.add_item(self.container)

        self.update_displays()

    def get_card_value(self, card: int):
        if card == 1:
            return 11  # Ace
        return 10 if card >= 11 else card

    def calculate_score(self, cards: list[int]):
        score = sum(self.get_card_value(card) for card in cards)
        ace_count = cards.count(1)

        while score > 21 and ace_count:
            score -= 10
            ace_count -= 1

        return score

    def format_hand(self, cards: list[int]):
        return " ".join(self.emoji_dict[card] for card in cards)

    def update_displays(self):
        dealer_score = self.calculate_score(self.dealer_cards)
        player_score = self.calculate_score(self.player_cards)

        self.dealer_display.content = (
            f"{self.format_hand(self.dealer_cards)} `[{dealer_score}]`"
        )
        self.player_display.content = (
            f"{self.format_hand(self.player_cards)} `[{player_score}]`"
        )

    def reveal_dealer(self):
        if 0 in self.dealer_cards:
            self.dealer_cards.remove(0)

    def disable_buttons(self):
        self.hit_button.disabled = True
        self.stand_button.disabled = True

    async def update_balance(self, interaction: discord.Interaction, amount: int):
        profile = await check_eco_profile(interaction.user, interaction.guild)

        await economy_profiles.update_one(
            {"user_id": profile["user_id"], "guild_id": profile["guild_id"]},
            {"$inc": {"currency": amount}}
        )

    async def end_game(self, interaction, title, color, payout=0):
        self.title.content = title
        self.container.accent_color = color
        self.disable_buttons()

        if payout:
            await self.update_balance(interaction, payout)

        self.update_displays()
        await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You do not have permission to interact with this game!",
                ephemeral=True
            )
            return False
        return True

    async def hit_callback(self, interaction: discord.Interaction):
        self.player_cards.append(random.randint(1, 13))
        self.update_displays()

        player_score = self.calculate_score(self.player_cards)

        if player_score > 21:
            await self.end_game(
                interaction,
                "### Player Bust!",
                discord.Color.red(),
                -abs(self.bet)
            )
            return

        await interaction.response.edit_message(view=self)

    async def stand_callback(self, interaction: discord.Interaction):
        self.reveal_dealer()

        while self.calculate_score(self.dealer_cards) < 17:
            self.dealer_cards.append(random.randint(1, 13))

        dealer_score = self.calculate_score(self.dealer_cards)
        player_score = self.calculate_score(self.player_cards)

        if dealer_score > 21:
            await self.end_game(
                interaction,
                "### Dealer Bust!",
                discord.Color.green(),
                abs(self.bet)
            )

        elif dealer_score == player_score:
            await self.end_game(
                interaction,
                "### Push!",
                discord.Color.yellow()
            )

        elif player_score > dealer_score:
            await self.end_game(
                interaction,
                "### Player Win!",
                discord.Color.green(),
                abs(self.bet)
            )

        else:
            await self.end_game(
                interaction,
                "### Dealer Win!",
                discord.Color.red(),
                -abs(self.bet)
            )