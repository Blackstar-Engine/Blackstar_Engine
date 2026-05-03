import discord
from discord.ext import commands

from utils.constants import economy_profiles
from utils.utils import check_funds, CheckEconomyProfile, get_max
from ui.economy.blackjack import Blackjack
from ui.economy.minesweeper import Minesweeper
from ui.economy.slots import Slots

import random
from datetime import datetime
import time

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_command(name="coinflip", description="Gamble currency in a coinflip")
    async def coinflip(self, ctx: commands.Context, choice: str, currency):
        await CheckEconomyProfile(ctx.author, ctx.guild)
        if isinstance(currency, int):
            pass
        else:
            if currency.lower() == "max" or "all":
                currency = await get_max(ctx.author, ctx.guild)
            else:
                return await ctx.send("Please enter a valid bet.")

        info = await economy_profiles.find_one({'user_id': ctx.author.id})

        if not await check_funds(currency, ctx.author, ctx.guild):
            return await ctx.send("You do not have enough money to make this bet.", ephemeral=True)
            
        if choice.lower() in ("heads", "head"):
            descision = "Heads"
        elif choice.lower() in ("tails", "tail"):
            descision = "Tails"
        else:
            return await ctx.send("Please choose either heads or tails.", ephemeral=True)
        
        number = random.randint(1, 100)

        face = "Heads" if number >= 50 else "Tails"

        if descision == face:
            current_currency = info.get("currency")
            if not current_currency:
                return await ctx.send("Failed to retrieve economy profile!", ephemeral=True)
            else:
                current_currency = int(info.get("currency"))
                new_balance = current_currency + currency

            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$set": {"currency": new_balance}} 
            )

            embed = discord.Embed(title=f"{face}!", description=f"You have earned {currency}✦", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            print(descision)
            current_currency = info.get("currency")
            if not current_currency:
                return await ctx.send("Failed to retrieve economy profile!", ephemeral=True)
            else:
                current_currency = int(info.get("currency"))
                new_balance = current_currency - currency

            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$set": {"currency": new_balance}} 
            )

            embed = discord.Embed(title=f"{face}!", description=f"You have lost {currency}✦", colour=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Get a daily reward")
    async def daily(self, ctx: commands.Context):
        await CheckEconomyProfile(ctx.author, ctx.guild)
        info = await economy_profiles.find_one({"user_id": ctx.author.id})
        
        last_claimed = info.get("last_claimed")

        if not last_claimed:
            return await ctx.send("Failed to retrieve economy profile", ephemeral=True)
        
        current_date = datetime.now().day

        if current_date != last_claimed:
            await economy_profiles.update_one(
                {"user_id": ctx.author.id},
                {
                    "$set": {
                        "last_claimed": datetime.now().day
                    },
                    "$inc": {
                        "currency": 250
                    }
                }
            )

            embed = discord.Embed(title=f"Claimed!", description=f"250✦ earned from daily reward!", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"Already Claimed", description=f"You have already claimed your daily reward today.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="steal", description="Steal money from another user")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, user: discord.User):
        if user == ctx.author:
            return await ctx.send("You cannot steal from yourself!", ephemeral=True)
        
        await CheckEconomyProfile(ctx.author, ctx.guild)
        author_info = await economy_profiles.find_one({"user_id": ctx.author.id})

        await CheckEconomyProfile(user, ctx.guild)
        user_info = await economy_profiles.find_one({"user_id": user.id})

        odds = random.randint(1, 100)
        if odds < 40:
            number = random.randint(20, 30)*0.01
            user_balance = user_info.get("currency")

            stolen_amount = round(user_balance*number)
            await economy_profiles.update_one(
                {
                    "user_id":user.id,
                },
                {
                    "$inc": {"currency": -stolen_amount}
                }
            )
            await economy_profiles.update_one(
                {
                    "user_id":ctx.author.id,
                },
                {
                    "$inc":{"currency":+stolen_amount}
                }
            )
            embed = discord.Embed(title=f"Robbed {user.name}!", description=f"You have stolen {stolen_amount}✦ from {user.name}!", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            number = random.randint(20, 30)*0.01
            author_balance = author_info.get("currency")

            stolen_amount = round(author_balance*number)       

            await economy_profiles.update_one(
                {
                    "user_id":ctx.author.id,
                },
                {
                    "$inc":{"currency":-stolen_amount}
                }
            )      
            embed = discord.Embed(title=f"You've been caught!", description=f"You have been caught by the police and lost {stolen_amount}✦", color=discord.Color.red())
            await ctx.send(embed=embed)    
    
    @steal.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            expires = int(time.time() + error.retry_after)
            embed = discord.Embed(title="Cooldown", description=f"You are currently on cooldown for robbing other users, try again in <t:{expires}:R>", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="balance", description="View your current amount of money")
    async def balance(self, ctx: commands.Context):
        await CheckEconomyProfile(ctx.author, ctx.guild)
        author_info = await economy_profiles.find_one({"user_id": ctx.author.id})
        balance = author_info.get("currency")
        
        embed = discord.Embed(description=f"You currently have {balance}✦", color=discord.Color.light_gray())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="blackjack", description="Gamble your money on a game of Blackjack")
    async def blackjack(self, ctx: commands.Context, currency):
        if isinstance(currency, int):
            pass
        else:
            if currency.lower() == "max" or "all":
                currency = await get_max(ctx.author, ctx.guild)
            else:
                return await ctx.send("Please enter a valid bet.")
            
        await CheckEconomyProfile(ctx.author, ctx.guild)
        if not await check_funds(currency, ctx.author, ctx.guild):
            return await ctx.send("You do not have enough money to make this bet.", ephemeral=True)
        view = Blackjack(ctx.author, currency)
        await ctx.send(view=view)

    @commands.hybrid_command(name="minesweeper", description="Gamble your money on a game of minesweeper")
    async def minesweeper(self, ctx: commands.Context, currency):
        if isinstance(currency, int):
            pass
        else:
            if currency.lower() == "max" or "all":
                currency = await get_max(ctx.author, ctx.guild)
            else:
                return await ctx.send("Please enter a valid bet.")
        await CheckEconomyProfile(ctx.author, ctx.guild)
        if not await check_funds(currency, ctx.author, ctx.guild):
            return await ctx.send("You do not have enough money to make this bet.", ephemeral=True)
        view = Minesweeper(ctx.author, currency)
        await ctx.send(view=view)

    @commands.hybrid_command(name="slots", description="Gamble your money on a game of slots")
    async def slots(self, ctx: commands.Context, currency):
        await CheckEconomyProfile(ctx.author, ctx.guild)
        if isinstance(currency, int):
            pass
        else:
            if currency.lower() == "max" or "all":
                currency = await get_max(ctx.author, ctx.guild)
            else:
                return await ctx.send("Please enter a valid bet.")
        if not await check_funds(currency, ctx.author, ctx.guild):
            return await ctx.send("You do not have enough money to make this bet.", ephemeral=True)
        view = Slots(currency)
        await ctx.send(view=view)










async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))