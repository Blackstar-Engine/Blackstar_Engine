import discord
from discord.ext import commands

from utils.constants import economy_profiles
from utils.utils import check_funds, get_max, check_currency, check_eco_profile
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
    async def coinflip(self, ctx: commands.Context, choice: str, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
            
        if choice.lower() in ("heads", "head"):
            descision = "Heads"
        elif choice.lower() in ("tails", "tail"):
            descision = "Tails"
        else:
            return await ctx.send("Please choose either heads or tails.", ephemeral=True)
        
        number = random.randint(1, 100)

        face = "Heads" if number >= 50 else "Tails"

        if descision == face:
            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$inc": {"currency": bet}} 
            )

            embed = discord.Embed(title=f"{face}!", description=f"You have earned {bet}✦", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$set": {"currency": -bet}} 
            )

            embed = discord.Embed(title=f"{face}!", description=f"You have lost {bet}✦", colour=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Get a daily reward")
    async def daily(self, ctx: commands.Context):
        profile = await check_eco_profile(ctx.author, ctx.guild)
        
        last_claimed = profile.get("last_claimed")
        
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

            embed = discord.Embed(title="Claimed!", description="250✦ earned from daily reward!", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Already Claimed", description="You have already claimed your daily reward today.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="steal", description="Steal money from another user")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, user: discord.User):
        if user == ctx.author:
            return await ctx.send("You cannot steal from yourself!", ephemeral=True)
        
        author_profile = await check_eco_profile(ctx.author, ctx.guild)

        user_profile = await check_eco_profile(user, ctx.guild)


        odds = random.randint(1, 100)
        if odds < 40:
            number = random.randint(20, 30)*0.01
            user_balance = user_profile.get("currency")

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
            author_balance = author_profile.get("currency")

            stolen_amount = round(author_balance*number)       

            await economy_profiles.update_one(
                {
                    "user_id":ctx.author.id,
                },
                {
                    "$inc":{"currency":-stolen_amount}
                }
            )      
            embed = discord.Embed(title="You've been caught!", description=f"You have been caught by the police and lost {stolen_amount}✦", color=discord.Color.red())
            await ctx.send(embed=embed)    
    
    @steal.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            expires = int(time.time() + error.retry_after)
            embed = discord.Embed(title="Cooldown", description=f"You are currently on cooldown for robbing other users, try again in <t:{expires}:R>", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            ctx.command.reset_cooldown(ctx)

    @commands.hybrid_command(name="balance", description="View your current amount of money")
    async def balance(self, ctx: commands.Context):
        profile = await check_eco_profile(ctx.author, ctx.guild)
        balance = profile.get("currency")
        
        embed = discord.Embed(description=f"You currently have {balance}✦", color=discord.Color.light_gray())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="blackjack", description="Gamble your money on a game of Blackjack")
    async def blackjack(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
        
        view = Blackjack(ctx.author, bet)
        await ctx.send(view=view)

    @commands.hybrid_command(name="minesweeper", description="Gamble your money on a game of minesweeper")
    async def minesweeper(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
        
        view = Minesweeper(ctx.author, bet)
        await ctx.send(view=view)

    @commands.hybrid_command(name="slots", description="Gamble your money on a game of slots")
    async def slots(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
        
        view = Slots(bet)
        await ctx.send(view=view)










async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))