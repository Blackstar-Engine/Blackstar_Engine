import os 
from dotenv import load_dotenv
from typing import Final
import logging
import sys
import motor.motor_asyncio
import re

load_dotenv()

class BlackstarConstants:
    '''
    Defines constants, they should always be capitals and set via the type of FINAL.
    '''
    ENVIRONMENT: Final[bool] = str(os.getenv('ENVIRONMENT'))
    TOKEN: Final[str] = str(os.getenv('TOKEN'))
    PREFIX: Final[str] = str(os.getenv('PREFIX'))
    MONGO_URI: Final[str] = str(os.getenv('MONGODB_URI'))

constants = BlackstarConstants()

LOARegFormat = r"^(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?$"
EMOJI_RE = re.compile(r"<a?:\w+:\d{17,20}>")
CHANNEL_RE = re.compile(r"<#\d{17,20}>")
USER_RE = re.compile(r"<@!?\d{17,20}>")
ROLE_RE = re.compile(r"<@&\d{17,20}>")
URL_RE = re.compile(r"https?://\S+")
profanity_list = [
                    "dick", "cock", "whore", "tranny", "faggot", "nig", "nigga", "fag",
                    "pussy", "vagina", "penis", "bitch", "fuck", "shit", "asshole",
                    "cunt", "nigger", "mother fucker", "titties", "titty", "boobs", "cum",
                    "tit", "douche", "douchebag", "blowjob", "handjob", "ass", "seman", "anel", "wanker",
                    "fucking", "fucker", "fucked", "fucks", "fuk"
                ]

client = motor.motor_asyncio.AsyncIOMotorClient(
    constants.MONGO_URI,
    compressors=['zlib'],
    maxPoolSize=150,
    minPoolSize=10,
    maxIdleTimeMS=300000,
    socketTimeoutMS=10000,
    connectTimeoutMS=10000,
    serverSelectionTimeoutMS=5000,
)

if constants.ENVIRONMENT == "PRODUCTION":
    db = client['blackstar_db']
else:
    db = client['blackstar_db_beta']

auto_replys = db.auto_replys
loa = db.loa
stored_loa = db.stored_loa
profiles = db.profiles
promotion_requests = db.promotion_requests
reaction_roles = db.reaction_roles
reminders = db.reminders
sessions = db.sessions
departments = db.departments

if constants.ENVIRONMENT == "PRODUCTION":
    loa_channel = 1412244838660968590
    loa_role = 1418067647177691156

    foundation_command = 1413208971304636597
    site_command = 1422416268585341049
    high_command = 1413226553982320713
    central_command = 1413226456968069180
    ia_id = 1413193754013073459
    wolf_id = 1371489554279825439
    overall_promotion_channel = 1412244417380618320
    profile_thread_channel = 1433946174791876740

    annoucement_role_id = 1413199178934259844
    chat_revive_role_id = 1450660091442368612
    dpr_display_role_id = 1460112895252758569
    game_night_role_id = 1413199433264398517
    misc_role_id = 1413199348753498222
    question_role_id = 1413199535081259079
    raid_role_id = 1457222250817392661
    session_role_id = 1456018515050893425
    vote_role_id = 1416830734760546476
else:
    loa_channel = 1454232138571448524
    loa_role = 1454233756545323200

    foundation_command = 1450297609515307134
    site_command = 1450297617073442816
    high_command = 1450297635994079375
    central_command = 1450297654662660156
    ia_id = 1450297786254889021
    wolf_id = 1371489554279825439
    overall_promotion_channel = 1450298055336136716
    profile_thread_channel = 1450298068162576525

    annoucement_role_id = 1450297860846387312
    chat_revive_role_id = 1450297899811475558
    dpr_display_role_id = 1450297861836247050
    game_night_role_id = 1450297865569304596
    misc_role_id = 1450297863145001030
    question_role_id = 1450297866991042701
    raid_role_id = 1470978604883116245
    session_role_id = 1470978602324590789
    vote_role_id = 1450297868459049131

if constants.ENVIRONMENT != "PRODUCTION":
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.theme import Theme

    console = Console(
        theme=Theme(
            {
                'logging.level.info': '#a6e3a1',
                'logging.level.debug': '#8aadf4',
                'logging.level.warning': '#f9e2af',
                'logging.level.error': '#f38ba8',
            }
        )
    )
    handler = RichHandler(tracebacks_width=200, console=console, rich_tracebacks=True)
else:
    handler = logging.StreamHandler()  # plain logs for prod


handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
level = logging.DEBUG if constants.ENVIRONMENT != "PRODUCTION" else logging.INFO

logger = logging.getLogger('Blackstar Engine')
logger.setLevel(level)
logger.addHandler(handler)
logger.propagate = False

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
discord_logger.addHandler(handler)
discord_logger.propagate = False

discord_http_logger = logging.getLogger('discord.http')
discord_http_logger.setLevel(logging.INFO)
discord_http_logger.addHandler(handler)
discord_http_logger.propagate = False


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception with full traceback
    logger.critical('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))