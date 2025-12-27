import discord
from discord.ext import commands
    
async def interaction_check(invoked: discord.User, interacted: discord.User):
    if invoked.id != interacted.id:
        raise commands.CheckFailure("Sorry but you can't use this button.")