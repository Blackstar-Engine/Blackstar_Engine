import discord
from discord.ext import commands
import uuid
from gtts import gTTS
import threading
from datetime import datetime

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
        raise commands.CommandError("Sorry but you can't use this button.")

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

def profile_creation_embed():
    dm_embed=discord.Embed(
        title="Welcome to Blackstar!",
        description="This is a quick tutorial on how we run things around these parts!",
        color=discord.Color.light_grey()
    )

    dm_embed.add_field(
        name="-Points Ranking System",
        value = "> To earn points you need to attend server sessions which are broadcasted ahead of time in [**#👾 sessions**](https://discord.com/channels/1411941814923169826/1434351873518993509), you can also earn points a variety of other ways such as hosting and co-hosting deployments or attending those deployments! Deployments will also be broadcasted in [**#📢 mission-briefing**](https://discord.com/channels/1411941814923169826/1412241044392640654), The best way to keep track of your points is by using the personal roster system to document all your attended events in one place, this can be found in [**#🪪 personal-roster**](https://discord.com/channels/1411941814923169826/1412295943654735952)",
        inline=False
    )

    dm_embed.add_field(
        name="-How to Enlist",
        value="> To enlist in a department you first need to make an enlistment form in [**#🪪 enlistment**](https://discord.com/channels/1411941814923169826/1433946174791876740), if you want to join another department you will need to enlist under that teams department category.",
        inline=False
    )

    dm_embed.add_field(
        name="-Document Links",
        value="For more information on a specific topic please see out server documents listed below.\n\n"
            "> [Stature of Regulation](https://trello.com/b/5LzFYOKb/name-stature-of-regulation)\n"
            "> [Code of Conduct](https://docs.google.com/document/d/1qUqOgbX8CoB3jzaIrIZxheqBpAeHk5HVLIP252cViac/edit?usp=sharing)\n"
            "> [Hierarchy & Points System](https://docs.google.com/document/d/1abd4Qq6CanUCLqjdmka5RmYEeD6GTFWGo2Czym0-nyo/edit?usp=sharing)\n"
            "> [Unit Database](https://docs.google.com/spreadsheets/d/1BLlkDxLW7GqPwVPmDuwpu-XBU98aY5_0ADX9QALXp4w/edit?usp=sharing)\n\n"
            "**For any other documents please refer to https://discord.com/channels/1411941814923169826/1418081211246575617 or a departments specified documents channel, you may also create a ticket to resolve any query or problem you may have.**\n\n"
            "**Thank you for being apart of the fun!**",
            inline=False
    )

    dm_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
    dm_embed.set_image(url="https://cdn.discordapp.com/attachments/1450512700034781256/1463307219159220316/Untitled_design_13.gif?ex=697be68b&is=697a950b&hm=53b2c67aedf52d6392e6c41c4d708e1a52b1c4c9bdda5c7c0f304c717e04cf04&")

    return dm_embed