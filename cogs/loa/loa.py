'''
loa_request = {
            'user_id': user.id,
            'guild_id': guild.id,
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'status': 'Pending'
            'moderator_id': None,
            
}
'''

import discord
from discord.ext import commands

class LOA(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # deletes message, sends custom message to user, admins able to ping user without bot

async def setup(bot: commands.Bot):
    await bot.add_cog(LOA(bot))