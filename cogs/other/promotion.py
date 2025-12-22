'''
promotion_request = {
                    'user_id': user.id,
                    'guild_id': guild.id,
                    'new_rank': new_rank,
                    'status': 'Pending',
                    'request_date': str(datetime.utcnow()),
                    'review_date': None,
                    'reviewed_by': None,
                    'comments': []
}
'''

import discord
from discord.ext import commands

class Promotions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(bot: commands.Bot):
    await bot.add_cog(Promotions(bot))