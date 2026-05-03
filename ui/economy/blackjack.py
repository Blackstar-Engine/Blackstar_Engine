import discord
from discord import ui
from discord.ext import commands

from utils.utils import CEP, CheckEconomyProfile
from utils.constants import economy_profiles

import random

class Blackjack(ui.LayoutView):
    def __init__(self, user, currency):
        super().__init__(timeout=None)
        self.currency = currency
        self.user = user
        self.emoji_dict = {
            0:"<:Unknown:1499985461106446448> ",
            1:"<:AceSpades:1499248426590933032>",
            2:"<:TwoOfSpades:1499248497461956628>",
            3:"<:ThreeOfClubs:1499248412128972831>",
            4:"<:FourOfHearts:1499248413844181092>",
            5:"<:FiveOfDiamonds:1499248415035363410>",
            6:"<:SixOfHearts:1499248416629456906>",
            7:"<:SevenOfSpades:1499248418030223431>",
            8:"<:EightOfDiamonds:1499248419510685807>",
            9:"<:NineOfSpades:1499248421067030558>",
            10:"<:TenOfClubs:1499249778620633240>",
            11:"<:JackOfSpade:1499248422459539466>",
            12:"<:QueenOfClubs:1499248423717834915>",
            13:"<:KingofHearts:1499250100919205960>",
        }

        self.dealer_cards = [random.randint(1, 13), 0]
        self.player_cards = [random.randint(1, 13)]

        self.dealer_display = ui.TextDisplay(
            " ".join(self.emoji_dict[c] for c in self.dealer_cards) + f" `[{sum(self.dealer_cards)}]`"
        )
        self.player_display = ui.TextDisplay(
            " ".join(self.emoji_dict[c] for c in self.player_cards) + f" `[{sum(self.player_cards)}]`"
        )

        self.hit_button = ui.Button(label="Hit", style=discord.ButtonStyle.danger)
        self.hit_button.callback = self.hit_callback

        self.stand_button = ui.Button(label="Stand", style=discord.ButtonStyle.success)
        self.stand_button.callback = self.stand_callback

        self.title = ui.TextDisplay("### Blackjack")

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

    async def hit_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("You do not have permisson to interact with this game!", ephemeral=True)
        card = random.randint(1, 13)
        self.player_cards.append(card)

        self.player_display.content = (
            " ".join(self.emoji_dict[c] for c in self.player_cards)
            + f" `[{sum(self.player_cards)}]`"
        )

        if sum(self.player_cards) > 21:
            self.title.content = "###  Player Bust!"
            self.container.accent_color = discord.Color.red()

            await CheckEconomyProfile(interaction.user, interaction.guild)
            
            await economy_profiles.update_one(
                {"user_id": self.user.id},
                {"$inc": {"currency": -self.currency}}
            )

            self.hit_button.disabled = True
            self.stand_button.disabled = True
        
        await interaction.response.edit_message(view=self)
    
    async def stand_callback(self, interaction: discord.Interaction):
        while sum(self.dealer_cards) < 17:
            card = random.randint(1, 13)
            self.dealer_cards.append(card)
        
        if sum(self.dealer_cards) > 21:
            self.dealer_cards.remove(0)
            self.dealer_display.content = (
                " ".join(self.emoji_dict[c] for c in self.dealer_cards)
                + f" `[{sum(self.dealer_cards)}]`"
            )
            self.title.content = "###  Dealer Bust!"
            self.container.accent_color = discord.Color.green()

            await CheckEconomyProfile(interaction.user, interaction.guild)
            
            await economy_profiles.update_one(
                {"user_id": self.user.id},
                {"$inc": {"currency": +self.currency}}
            )

            self.hit_button.disabled = True
            self.stand_button.disabled = True
        else:
            self.dealer_cards.remove(0)
            player_score = sum(self.player_cards) if sum(self.player_cards) <= 21 else 0
            dealer_score = sum(self.dealer_cards) if sum(self.dealer_cards) <= 21 else 0

            if player_score > dealer_score:
                self.dealer_display.content = (
                    " ".join(self.emoji_dict[c] for c in self.dealer_cards)
                    + f" `[{sum(self.dealer_cards)}]`"
                )

                self.title.content = "###  Player Win!"
                self.container.accent_color = discord.Color.green()

                info = await economy_profiles.find_one({"user_id":interaction.user.id})
                if not info:
                    await CEP(self.user, interaction.guild)
                    info = await economy_profiles.find_one({"user_id":interaction.user.id})
                
                await economy_profiles.update_one(
                    {"user_id": self.user.id},
                    {"$inc": {"currency": +self.currency}}
                )

                self.hit_button.disabled = True
                self.stand_button.disabled = True   
            else:
                self.dealer_display.content = (
                    " ".join(self.emoji_dict[c] for c in self.dealer_cards)
                    + f" `[{sum(self.dealer_cards)}]`"
                )
                self.title.content = "###  Dealer Win!"
                self.container.accent_color = discord.Color.red()

                await CheckEconomyProfile(interaction.user, interaction.guild)
                
                await economy_profiles.update_one(
                    {"user_id": self.user.id},
                    {"$inc": {"currency": -self.currency}}
                )

                self.hit_button.disabled = True
                self.stand_button.disabled = True                         
        
        await interaction.response.edit_message(view=self)



            
