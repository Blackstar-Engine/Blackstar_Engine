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
MESSAGE_CODE_RE = re.compile(r"^(\[[^\]]+\]|\*\*[\s\S]+?\*\*)")#  \*\*(.*?)\*\* | This will check for ****
profanity_list = [
                    "dick", "cock", "whore", "tranny", "faggot", "nig", "nigga", "fag",
                    "pussy", "vagina", "penis", "bitch", "fuck", "shit", "asshole",
                    "cunt", "nigger", "mother fucker", "titties", "titty", "boobs", "cum",
                    "tit", "douche", "douchebag", "blowjob", "handjob", "ass", "seman", "anel", "wanker",
                    "fucking", "fucker", "fucked", "fucks", "fuk"
                ]
whitelisted_guilds = [1411941814923169826, 1450297281088720928]

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
enlistment_requests = db.enlistment_requests
point_requests = db.point_requests
departments = db.departments
ids = db.ids
active_sessions = db.active_sessions

if constants.ENVIRONMENT == "PRODUCTION":
    annoucement_role_id = 1413199178934259844
    misc_role_id = 1413199348753498222
    game_night_role_id = 1413199433264398517
    question_role_id = 1413199535081259079
    vote_role_id = 1416830734760546476
    chat_revive_role_id = 1450660091442368612
    dpr_display_role_id = 1460112895252758569
    raid_role_id = 1457222250817392661
    session_role_id = 1456018515050893425
    external_role_id = 1481419195903381716
else:
    annoucement_role_id = 1450297860846387312
    dpr_display_role_id = 1450297861836247050
    misc_role_id = 1450297863145001030
    game_night_role_id = 1450297865569304596
    question_role_id = 1450297866991042701
    vote_role_id = 1450297868459049131
    chat_revive_role_id = 1450297899811475558
    raid_role_id = 1470978604883116245
    session_role_id = 1470978602324590789
    external_role_id = 1481485568784470127

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