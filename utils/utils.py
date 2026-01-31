import discord
from discord.ext import commands

from utils.constants import constants

from utils.constants import (
    foundation_command,
    site_command,
    high_command,
    central_command,
    wolf_id
)
    
async def interaction_check(invoked: discord.User, interacted: discord.User):
    if invoked.id != interacted.id:
        raise commands.CheckFailure("Sorry but you can't use this button.")

def has_approval_perms(member: discord.Member) -> bool:
    allowed_roles = {
        foundation_command,
        site_command,
        high_command,
        central_command,
    }

    if member.id == wolf_id:
        return True

    return any(role.id in allowed_roles for role in member.roles)