import discord
from discord.ext import commands
from discord import ui
import uuid
import edge_tts
import threading
from datetime import datetime, timezone
import os
import asyncio
from dateutil import parser
import re
import unicodedata
from utils.constants import (
    profiles,
    departments,
    URL_RE,
    ROLE_RE,
    USER_RE,
    CHANNEL_RE,
    EMOJI_RE,
    BlackstarConstants,
    ids
)

tts_lock = threading.Lock()
constants = BlackstarConstants()

def interaction_check(invoked: discord.User, interacted: discord.User):
    if invoked.id != interacted.id:
        raise commands.CommandError("Sorry but you can't use this button.")

async def has_approval_perms(member: discord.Member, level: int) -> bool:
    results = await fetch_id(member.guild.id, ["foundation_command", "site_command", "high_command", "central_command", "ia_id", "drm_id", "ghost_id", "option_id", "wolf_id"])
    match level:
        case 1:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"],
                results["ia_id"]
            }
        case 2:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"],
                results["drm_id"]
            }
        case 3:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"]
            }
        case 4:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"]
            }
        case 5:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"]
            }
        case 6:
            allowed_roles = {
                results["foundation_command"]
            }


    if member.id == results["wolf_id"]:
        return True

    if constants.ENVIRONMENT == "DEVELOPMENT" and member.id in (results["ghost_id"], results["option_id"]):
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

async def fetch_id(guild_id, id_names: list[str]):
    results = await ids.find({"guild_id": int(guild_id), "key": {"$in": id_names}}).to_list(length=None)

    return {result["key"]: result["value"] for result in results}

async def tts_to_file(user: discord.Member, last_speaker, last_message_time, text: str) -> str:
    filename = f"tts_{uuid.uuid4()}.mp3"

    user_display = unicodedata.normalize("NFKD", user.display_name)

    user_display = user_display.encode("ascii", "ignore").decode("ascii")

    display_name = clean_username(user_display)

    if last_speaker == user.id and last_message_time < 30:
        text = f"{text}"
    else:
        text = f"{display_name} said {text}"

    voice = "en-AU-WilliamMultilingualNeural"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

    return filename

def clean_username(name: str) -> str:
    return re.sub(r"\[.*?\]\s*", "", name).strip()

def profile_creation_embed():
    dm_embed=discord.Embed(
        title="Congrats on the Enlistment!",
        description="This is a quick tutorial on how we run things around these parts!",
        color=discord.Color.light_grey()
    )

    dm_embed.add_field(
        name="-Personal Roster",
        value="> We require everyone to create there own roster, please head to https://discord.com/channels/1411941814923169826/1412295943654735952 and following the guidelines."
    )

    dm_embed.add_field(
        name="-Our Point System",
        value = "> To get points you need to attend sessions, deployments, or trainings. Everything is **1 point** unless notified otherwise. MVP is **1.5 points**. You can than request those with `!points request <number> <proof>`",
        inline=False
    )

    dm_embed.add_field(
        name="-Document Links",
        value="Here are some important documents to review:\n"
            "> [Stature of Regulation](https://trello.com/b/5LzFYOKb/name-stature-of-regulation)\n"
            "> [Code of Conduct](https://docs.google.com/document/d/1qUqOgbX8CoB3jzaIrIZxheqBpAeHk5HVLIP252cViac/edit?usp=sharing)\n"
            "> [Hierarchy & Points System](https://docs.google.com/document/d/1abd4Qq6CanUCLqjdmka5RmYEeD6GTFWGo2Czym0-nyo/edit?usp=sharing)\n"
            "> [BSC Charter](https://docs.google.com/document/d/1jVVxMcG8cB-lGta7gRATSimle2s2PuQZz7WnHOxY8d8/edit?usp=sharing)\n"
            "**For any other documents please refer to https://discord.com/channels/1411941814923169826/1418081211246575617**",
            inline=False
    )

    dm_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
    dm_embed.set_image(url="https://cdn.discordapp.com/attachments/1450512700034781256/1463307219159220316/Untitled_design_13.gif?ex=697be68b&is=697a950b&hm=53b2c67aedf52d6392e6c41c4d708e1a52b1c4c9bdda5c7c0f304c717e04cf04&")

    return dm_embed

def tts_match_object(message: discord.Message):
    text = message.content

    # Replace discord formatted things
    text = EMOJI_RE.sub("emoji", text)
    text = CHANNEL_RE.sub("channel", text)
    text = USER_RE.sub("user", text)
    text = ROLE_RE.sub("role", text)

    # Replace links anywhere in message
    text = URL_RE.sub("link", text)

    # Replace attachments (images, files, etc.)
    if message.attachments:
        if text:
            text += " with an attachment"
        else:
            text = "an attachment"

    return text.strip()

def tts_logic(queue: asyncio.Queue, vc: discord.VoiceClient, file):
    # File was deleted by clear() — skip it
    if not os.path.exists(file):
        queue.task_done()
        return None

    if not vc or not vc.is_connected():
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        queue.task_done()
        return None

    try:
        source = discord.FFmpegPCMAudio(file)
        return source

    except Exception as e:
        print(f"FFmpeg failed to open {file}: {e}")
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        queue.task_done()
        return None

def generate_timestamp(date_str: str):
    dt = parser.parse(date_str)
    dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())

async def role_user(ctx: commands.Context, department: str):
    unit = department.upper()
    if isinstance(ctx, discord.Interaction):
        user = ctx.user
    else:
        user = ctx.author

    department = await fetch_department(ctx, unit)

    if not department:
        embed = discord.Embed(title="No Department Found", description=f"I couldd not find a department with the name `{unit}`", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return False

    overall_role_id = department.get('role_id')
    first_rank_role_id = department.get('first_rank_id')

    results = await fetch_id(ctx.guild.id, ['mtf_overall_role_id'])

    if unit.startswith("MTF"):
        mtf_overall_role_obj = ctx.guild.get_role(results['mtf_overall_role_id'])

    overall_role_obj = ctx.guild.get_role(overall_role_id)
    first_rank_role_obj = ctx.guild.get_role(first_rank_role_id)

    if not overall_role_obj or not first_rank_role_obj:
        embed = discord.Embed(title="Role Not Found", description=f"I could not find the overall or first rank role for the `{unit}` department. Please make sure they are setup correctly.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return False
    elif overall_role_obj in user.roles and first_rank_role_obj in user.roles:
        embed = discord.Embed(title="User Already Has Roles", description=f"{user.mention} is already in `{unit}`.", color=discord.Color.yellow())
        await ctx.send(embed=embed, ephemeral=True)
        return False

    if unit.startswith("MTF"):
        await user.add_roles(mtf_overall_role_obj, overall_role_obj, first_rank_role_obj, reason=f"Role User Command used by {ctx.author}")
    else:
        await user.add_roles(overall_role_obj, first_rank_role_obj, reason=f"Role User Command used by {ctx.author}")
    
    return True

async def log_action(ctx: commands.Context, log_type: str, **kwargs):
    if isinstance(ctx, discord.Interaction):
        author = ctx.user
        command_name = ctx.command.name if ctx.command else "Unknown"
    else:
        author = ctx.author
        command_name = ctx.command.qualified_name if ctx.command else "Unknown"

    log_embed = discord.Embed(title="", description="", color=discord.Color.light_grey())
    log_embed.set_footer(text=f"Blackstar Engine Logging • {datetime.now().date()}")

    match log_type:
        case "point_deduction":
            results = await fetch_id(ctx.guild.id, ["point_deduction_log"])
            log_embed.title = "Point Deduction"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Points Reduced:** {kwargs['points']}\n**Command:** {command_name}"
        case "point_addition":
            results = await fetch_id(ctx.guild.id, ["point_addition_log"])
            log_embed.title = "Point Addition"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Points Added:** {kwargs['points']}\n**Command:** {command_name}"
        case "department":
            results = await fetch_id(ctx.guild.id, ["department_log"])
            log_embed.title = "Department Updated"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Updated Department:** {kwargs['department']}\n**Command:** {command_name}"
        case "mod_command":
            results = await fetch_id(ctx.guild.id, ["mod_command_log"])
            log_embed.title = "Mod Command Used"
            log_embed.description = f"**Moderator:** {author.mention}\n**Command:** {command_name}"
    
    try:
        _, first_value = next(iter(results.items()), None)
        channel = await ctx.guild.fetch_channel(int(first_value))

        await channel.send(embed=log_embed)
    except Exception:
        pass
