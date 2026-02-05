import discord
from discord.ext import commands
import uuid
from gtts import gTTS
import threading

from utils.constants import (
    foundation_command,
    site_command,
    high_command,
    central_command,
    wolf_id,
    profiles,
    departments
)

tts_lock = threading.Lock()

async def interaction_check(invoked: discord.User, interacted: discord.User):
    if invoked.id != interacted.id:
        raise discord.errors.InvalidData("Sorry but you can't use this button.")

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

async def fetch_profile(ctx: commands.Context, send_message: bool = True):
    profile = await profiles.find_one({'guild_id': ctx.guild.id, 'user_id': ctx.author.id})

    if not profile:
        if send_message:
            embed = discord.Embed(title="", description="Profile Not Found", color=discord.Color.dark_embed())
            await ctx.send(embed=embed)

        return False
    
    return profile

async def fetch_department(ctx: commands.Context, department: str):
    department_doc = await departments.find_one({
            "$or": [
                {"name": department},
                {"display_name": department}
            ]
        })
    
    if not department_doc:
        embed = discord.Embed(title="", description="Department not found.", color=discord.Color.dark_embed())
        await ctx.send(embed=embed)
        return False
    
    return department_doc

def fetch_unit_options(profile):
    options = []
    units = dict(profile.get("unit", {}))

    for unit, data in units.items():
        if data.get("is_active"):
            options.append(discord.SelectOption(label=unit))
    
    if options == []:
        options.append(discord.SelectOption(label="No Active Units", value="no_units"))
    
    return options

def tts_to_file(user, text: str) -> str:
    filename = f"tts_{uuid.uuid4()}.mp3"
    text = f"{user} said {text}"

    with tts_lock:
        tts = gTTS(text=text, lang="en", tld="com.au")
        tts.save(filename)

    return filename