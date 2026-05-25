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
    
    @commands.hybrid_group(name="economy")
    async def eco_main(self, ctx: commands.Context):
        return
    
    @eco_main.command(name="coinflip", description="Gamble currency in a coinflip")
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
        
        face = random.choice(["Heads", "Tails"])

        if descision == face:
            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$inc": {"currency": +bet}} 
            )

            embed = discord.Embed(title=f"{face}!", description=f"You have earned {bet}✦", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await economy_profiles.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
                {"$inc": {"currency": -bet}} 
            )


            embed = discord.Embed(title=f"{face}!", description=f"You have lost {bet}✦", colour=discord.Color.red())
            await ctx.send(embed=embed)


    @eco_main.command(name="daily", description="Get a daily reward")
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

    @eco_main.command(name="steal", description="Steal money from another user")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def steal(self, ctx: commands.Context, user: discord.User):
        if user == ctx.author:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You cannot steal from yourself!", ephemeral=True)
        
        # load or create the authors profile
        author_profile = await check_eco_profile(ctx.author, ctx.guild)
        # check the balance to see if its 0 or below
        author_balance = author_profile.get("currency", 0)

        # load or create the users profile
        user_profile = await check_eco_profile(user, ctx.guild)
        # check the balance to see if its 0 or below
        user_balance = user_profile.get("currency", 0)
        if user_balance <= 0:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("This users balance is 0 or below, please try someone else!")

        odds = random.randint(1, 100) # randomly gen odds from 1 to 100

        number = random.randint(10, 30)*0.01 # randomly gen a % from 10 to 30%
        stolen_amount = abs(round(user_balance*number)) # calc the stolen amount by taking the % from the users profile, makeing sure its > 0
        lost_amount = abs(round(author_balance*number))
        if odds < 40: # if its below 40% they win
            await economy_profiles.update_one(
                {
                    "user_id":user.id,
                },
                {
                    "$inc": {"currency": +stolen_amount}
                }
            )
            embed = discord.Embed(title=f"Robbed {user.name}!", description=f"You have stolen {stolen_amount}✦ from {user.name}!", color=discord.Color.green())
            await ctx.send(embed=embed)
        else: # if its not below 40% they loose
            await economy_profiles.update_one(
                {
                    "user_id":ctx.author.id,
                },
                {
                    "$inc":{"currency":-lost_amount}
                }
            )      
            embed = discord.Embed(title="You've been caught!", description=f"You have been caught by the police and lost {lost_amount}✦", color=discord.Color.red())
            await ctx.send(embed=embed)    
    
    @steal.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            expires = int(time.time() + error.retry_after)
            embed = discord.Embed(title="Cooldown", description=f"You are currently on cooldown for robbing other users, try again in <t:{expires}:R>", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            ctx.command.reset_cooldown(ctx)

    @eco_main.command(name="balance", description="View your current amount of money")
    async def balance(self, ctx: commands.Context):
        profile = await check_eco_profile(ctx.author, ctx.guild)
        balance = profile.get("currency")
        
        embed = discord.Embed(description=f"You currently have {balance}✦", color=discord.Color.light_grey())
        await ctx.send(embed=embed)
    
    @eco_main.command(name="gift", description="Gift money to a another user")
    async def gift_points(self, ctx: commands.Context, user: discord.Member, amount: int):
        amount = abs(amount)
        author_profile = await check_eco_profile(ctx.author, ctx.guild)
        author_balance = author_profile.get("currency")
        if author_balance <= 0:
            return await ctx.send("It looks like your balance is below 0!", ephemeral=True)
        
        if author_balance < amount:
            return await ctx.send("It looks like you dont have that much in your account!", ephemeral=True)

        await check_eco_profile(user, ctx.guild)

        await economy_profiles.update_one(
            {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
            {"$inc": {"currency": -amount}}
        )

        await economy_profiles.update_one(
            {"user_id": user.id, "guild_id": ctx.guild.id},
            {"$inc": {"currency": amount}}
        )

        embed = discord.Embed(
            title="Successfully Gifted",
            description=f"You just gifted points to {user.mention}! Points on your profile have been reduced!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @eco_main.command(name="blackjack", description="Gamble your money on a game of Blackjack")
    async def blackjack(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
    
        await economy_profiles.update_one(
            {"user_id": ctx.author.id, "guild_id": ctx.guild.id},
            {"$inc": {"currency": -bet}}
        )    
        
        view = Blackjack(ctx.author, bet)
        await ctx.send(view=view)

    @eco_main.command(name="minesweeper", description="Gamble your money on a game of minesweeper")
    async def minesweeper(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
             
        await economy_profiles.update_one(
            {
                "user_id": ctx.author.id,
                "guild_id": ctx.guild.id
            },
            {
                "$inc": {
                    "currency": -bet
                }
            }
        )
        
        view = Minesweeper(ctx.author, bet)
        await ctx.send(view=view)

    @eco_main.command(name="slots", description="Gamble your money on a game of slots")
    async def slots(self, ctx: commands.Context, bet):
        bet, _ = await check_currency(ctx, bet, ctx.author, ctx.guild)
        if not bet:
            return
        
        await economy_profiles.update_one(
            {
                "user_id": ctx.author.id,
                "guild_id": ctx.guild.id
            },
            {
                "$inc": {
                    "currency": -bet
                }
            }
        )
        
        view = Slots(ctx.author, bet)
        await ctx.send(view=view)

    @eco_main.command(name="test", description="test")
    async def test(self, ctx: commands.Context, amount: int):
        await economy_profiles.update_one(
            {
                "user_id": ctx.author.id,
                "guild_id": ctx.guild.id
            },
            {
                "$set": {
                    "currency":amount
                }
            }
        )        
        await ctx.send('done')









async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))