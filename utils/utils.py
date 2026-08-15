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
from datetime import datetime, timedelta
from utils.constants import (
    profiles,
    departments,
    URL_RE,
    ROLE_RE,
    USER_RE,
    CHANNEL_RE,
    EMOJI_RE,
    BlackstarConstants,
    ids,
    economy_profiles,
    bypassed_users,
    permission_rules,
    whitelisted_guilds
)
from edge_tts.exceptions import NoAudioReceived
from utils.custom_errors import PermissionDenied

tts_lock = threading.Lock()
constants = BlackstarConstants()

def interaction_check(invoked: discord.User, interacted: discord.User):
    if invoked.id != interacted.id:
        raise commands.CommandError("Sorry but you can't use this button.")

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
        if isinstance(ctx, discord.Interaction):
            try:
                await ctx.response.send_message(embed=embed, ephemeral=True)
            except discord.HTTPException:
                await ctx.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed, ephemeral=True)
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

async def fetch_id(guild_id, id_key: str):
    results = await ids.find_one({"guild_id": int(guild_id), "key": id_key})

    return results

async def tts_to_file(user: discord.Member, last_speaker, last_message_time, text: str) -> str:
    filename = f"tts_{uuid.uuid4()}.mp3"

    user_display = unicodedata.normalize("NFKD", user.display_name)

    user_display = user_display.encode("ascii", "ignore").decode("ascii")

    display_name = clean_username(user_display)

    if last_speaker == user.id and last_message_time < 30:
        text = f"{text}"
    else:
        text = f"{display_name} said {text}"

    voice = "en-CA-LiamNeural"

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filename)
    except NoAudioReceived:
        pass

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
        return False

    overall_role_id = department.get('role_id')
    first_rank_role_id = department.get('first_rank_id')

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

    await user.add_roles(overall_role_obj, first_rank_role_obj, reason=f"Role User Command used by {ctx.author}")
    
    return True

async def log_action(ctx: commands.Context, log_type: str, **kwargs):
    if isinstance(ctx, discord.Interaction):
        author = ctx.user
    else:
        author = ctx.author

    log_embed = discord.Embed(title="", description="", color=discord.Color.light_grey())
    log_embed.set_footer(text=f"Blackstar Engine Logging • {datetime.now().date()}")

    results = await fetch_id(ctx.guild.id, "logging_channels")

    match log_type:
        case "point_deduction":
            channel_id = results["values"].get("point_deduction_log", 0)
            log_embed.title = "Point Deduction"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Points Reduced:** {kwargs['points']}\n**Command:** {kwargs['command_name']}"
        case "point_addition":
            channel_id = results["values"].get("point_addition_log", 0)
            log_embed.title = "Point Addition"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Points Added:** {kwargs['points']}\n**Command:** {kwargs['command_name']}"
        case "department":
            channel_id = results["values"].get("department_log", 0)
            log_embed.title = "Department Updated"
            log_embed.description = f"**Moderator:** {author.mention}\n**User:** <@{kwargs['user_id']}>\n**Updated Department:** {kwargs['department']}\n**Command:** {kwargs['command_name']}"
        case "mod_command":
            channel_id = results["values"].get("mod_command_log", 0)
            log_embed.title = "Mod Command Used"
            log_embed.description = f"**Moderator:** {author.mention}\n**Command:** {kwargs['command_name']}\n\n**Arguments:** {kwargs['arguments']}"
    
    try:
        channel = await ctx.guild.fetch_channel(int(channel_id))

        await channel.send(embed=log_embed)
    except Exception:
        pass

async def create_eco_profile(user: discord.Member, guild: discord.Guild):
    dt = (datetime.now() - timedelta(days=1)).day
    eco_doc = {
        "user_id":user.id, 
        "guild_id":guild.id,
        "currency":500, 
        "last_claimed":dt
    }
    await economy_profiles.insert_one(eco_doc)

    return eco_doc

async def check_eco_profile(user: discord.Member, guild: discord.Guild):
    profile = await economy_profiles.find_one({"user_id":user.id, "guild_id":guild.id})
    if not profile:
        profile = await create_eco_profile(user, guild)
    
    return profile

async def check_funds(claim: int, user: discord.Member, guild: discord.Guild):
    profile = await check_eco_profile(user, guild)
    currency = profile.get("currency")

    if currency >= claim:
        return True
    elif currency < 0:
        return False
    else:
        return False
    
async def get_max(user: discord.Member, guild: discord.Guild):
    profile = await check_eco_profile(user, guild)
    return profile.get("currency")

async def check_currency(ctx: commands.Context, bet, user: discord.Member, guild: discord.Guild):
    profile = await check_eco_profile(user, guild)

    try:
        bet = int(bet)
    except ValueError:
        if bet.lower() in ("max", "all"):
            bet = await get_max(ctx.author, ctx.guild)
        else:
            await ctx.send("Please enter a valid bet.")
            return False, profile
    
    bet = int(bet)
    
    if bet <= 0:
        await ctx.send("Please enter a bet greater than 0.")
        return False, profile

    if not await check_funds(bet, ctx.author, ctx.guild):
        await ctx.send("You do not have enough money to make this bet.", ephemeral=True)
        return False, profile
    
    return bet, profile

async def get_gift_limit(ctx: commands.Context, user: discord.Member | None = None):
    target_user = user or ctx.author

    if int(target_user.id) == int(ctx.guild.owner.id):
        return 999999999999999

    user_role_ids = {role.id for role in target_user.roles}
    matching_tiers = [
        tier for tier in ctx.bot.permission_tiers
        if tier.get("guild_id") == ctx.guild.id
        and user_role_ids & set(tier.get("role_ids", []))
    ]

    if not matching_tiers:
        return False

    matching_tier = max(matching_tiers, key=lambda tier: tier.get("rank", 0))

    if not matching_tier.get("can_gift_points", False):
        return False

    gift_amount = matching_tier.get("gift_points_amount", 0)
    if gift_amount <= 0:
        return False

    return gift_amount

def find_override(bot: commands.Bot, ctx: commands.Context, scope_type: str, scope_key: str):
    if isinstance(ctx, discord.Interaction):
        user = ctx.user
    else:
        user = ctx.author

    user_id = user.id
    guild_id = ctx.guild.id
    user_role_ids = {role.id for role in user.roles}
    overrides = bot.permission_overrides

    if scope_key is None:
        return None
    
    scoped = [
        r for r in overrides
        if r.get("guild_id") == guild_id
        and r.get("scope_type") == scope_type
        and r.get("scope_key") == scope_key
    ]

    user_override = next(
        (r for r in scoped if r.get("target_type") == "user" and r.get("target_id") == user_id),
        None
    )
    if user_override:
        effect = True if user_override.get("effect", False) == "allow" else False
        return effect

    role_override = next(
        (r for r in scoped if r.get("target_type") == "role" and r.get("target_id") in user_role_ids),
        None
    )
    if role_override:
        effect = True if role_override.get("effect", False) == "allow" else False
        return effect
    
def find_rule(bot: commands.Bot, ctx: commands.Context, scope_type: str, scope_key: str):
    guild_id = ctx.guild.id
    rules = bot.permission_rules

    if scope_key is None:
        return None
    
    return next(
        (
            r for r in rules
            if r.get("guild_id") == guild_id
            and r.get("scope_type") == scope_type
            and r.get("scope_key") == scope_key
        ),
        None
    )

def find_tier(bot: commands.Bot, ctx: commands.Context, rank = None, name = None):
    tiers = bot.permission_tiers
    guild_id = ctx.guild.id

    if name is None:
        tier_doc = next(
            (
                t for t in tiers
                if t.get("guild_id") == guild_id
                and t.get("rank") == rank
            ),
            None
        )

    elif rank is None:
        tier_doc = next(
            (
                t for t in tiers
                if t.get("guild_id") == guild_id
                and t.get("name") == name
            ),
            None
        )
    else:
        tier_doc = next(
            (
                t for t in tiers
                if t.get("guild_id") == guild_id
                and t.get("name") == name
                and t.get("rank") == rank
            ),
            None
        )
    
    return tier_doc

def find_tier_plus(bot: commands.Bot, ctx: commands.Context, min_rank: int):
    tiers = bot.permission_tiers
    guild_id = ctx.guild.id

    matching_ranks = [
        t for t in tiers
        if t.get("guild_id") == guild_id
        and t.get("rank") >= min_rank
    ]

    return matching_ranks

def get_user_permissions(bot: commands.Bot, ctx: commands.Context, user: discord.Member):
    tiers = bot.permission_tiers
    guild_id = ctx.guild.id
    user_role_ids = {role.id for role in user.roles}
    

    matching_ranks = [
        t.get("rank", 0) for t in tiers
        if t.get("guild_id") == guild_id
        and user_role_ids & set(t.get("role_ids", []))
    ]

    return_value = int(max(matching_ranks, default=0))

    return return_value

def permissions():
    async def predicate(ctx: commands.Context):
        command = ctx.command.qualified_name
        cog = ctx.cog.qualified_name if ctx.cog else None

        command_override = find_override(ctx.bot, ctx, "command", command)
        if command_override is not None:
            return command_override
        
        cog_override = find_override(ctx.bot, ctx, "feature", cog)
        if cog_override is not None:
            return cog_override
        
        rule = find_rule(ctx.bot, ctx, "command", command)
        if rule is None:
            rule = find_rule(ctx.bot, ctx, "feature", cog)
        
        if rule is not None:
            required_rank = int(rule.get("min_rank", 0))
            if get_user_permissions(ctx.bot, ctx, ctx.author) >= required_rank:
                return True
            
        if ctx.author.guild_permissions.administrator or ctx.author.id in bypassed_users:
            return True
        
        raise PermissionDenied("fallback")
    
    check = commands.check(predicate)

    def decorator(func):
        func.permission_managed = True
        return check(func)

    return decorator

async def get_permission_node(ctx: commands.Context, key: str):
    if not key:
        return False

    if isinstance(ctx, discord.Interaction):
        user = ctx.user
        bot = ctx.client
    else:
        user = ctx.author
        bot = ctx.bot

    if not ctx.guild:
        return False

    # if user.guild_permissions.administrator or user.id in bypassed_users:
    #     return True

    result = await permission_rules.find_one({
        "guild_id": ctx.guild.id,
        "scope_type": "permission",
        "scope_key": key
    })

    if not result:
        return False

    required_rank = int(result.get("min_rank", 0))
    return get_user_permissions(bot, ctx, user) >= required_rank

async def is_whitelisted(guild: discord.Guild, bot: commands.Bot):
    if guild.id in whitelisted_guilds:
        return True

    message = "This is a whitelisted bot. You are not allowed to invite me."

    try:
        await guild.owner.send(message)
    except (discord.Forbidden, discord.HTTPException, AttributeError):
        me = guild.me or guild.get_member(bot.user.id)

        for channel in guild.text_channels:
            perms = channel.permissions_for(me)

            if perms.view_channel and perms.send_messages:
                try:
                    await channel.send(message)
                    break
                except (discord.Forbidden, discord.HTTPException):
                    continue

    await guild.leave()
    return False

def format_permission_tier(guild_id: int, name: str, rank: int, role_ids: list[int], can_gift_points: bool, gift_points_amount: int):
    return {
        "guild_id": guild_id,
        "name": name,
        "rank": rank,
        "role_ids": role_ids,
        "can_gift_points": can_gift_points,
        "gift_points_amount": gift_points_amount
    }

def format_permission_rule(guild_id: int, scope_type: str, scope_key: str, min_rank: int):
    return {
        "guild_id": guild_id,
        "scope_type": scope_type,
        "scope_key": scope_key,
        "min_rank": min_rank
    }

def format_permission_override(guild_id: int, scope_type: str, scope_key: str, target_type: str, target_id: int, effect: str):
    return {
        "guild_id": guild_id,
        "scope_type": scope_type,
        "scope_key": scope_key,
        "target_type": target_type,
        "target_id": target_id,
        "effect": effect
    }

def format_permission_node(guild_id: int, scope_type: str, scope_key: str, min_rank: int):
    return {
        "guild_id": guild_id,
        "scope_type": scope_type,
        "scope_key": scope_key,
        "min_rank": min_rank
    }

def format_id(guild_id: int, key: str, values):
    return {
        "guild_id": guild_id,
        "key": key,
        "values": values
    }