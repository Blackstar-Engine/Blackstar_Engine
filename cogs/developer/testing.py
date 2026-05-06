import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime
from utils.utils import has_approval_perms
from utils.constants import economy_profiles

class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        all_profiles = await economy_profiles.find({"guild_id": ctx.guild.id}).to_list(length=None)

        profile_count = 0
        for profile in all_profiles:
            try: 
                await economy_profiles.update_one({"user_id": profile.get("user_id"), "guild_id": profile.get("guild_id")}, {"$set": {"currency": 1000}})
                profile_count += 1
            except Exception:
                pass
        
        await ctx.send(f"All profiles have been reset to 1k: {profile_count} profiles\norg number: {len(all_profiles)}")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))