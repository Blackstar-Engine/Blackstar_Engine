import os
from dotenv import load_dotenv
import motor.motor_asyncio

load_dotenv()

class BlackstarConstants:
    def token(self) -> str:
        return str(os.getenv('TOKEN'))
    
    def prefix(self) -> str:
        return str(os.getenv('PREFIX'))
    
    def mongodb_uri(self) -> str:
        return str(os.getenv('MONGODB_URI'))

arcconstants = BlackstarConstants()

client = motor.motor_asyncio.AsyncIOMotorClient(
    arcconstants.mongodb_uri(),
    compressors=['zlib'],
    maxPoolSize=150,
    minPoolSize=10,
    maxIdleTimeMS=300000,
    socketTimeoutMS=10000,
    connectTimeoutMS=10000,
    serverSelectionTimeoutMS=5000,
)

db = client['blackstar_db']

auto_replys = db.auto_replys
loa = db.loa
stored_loa = db.stored_loa
profiles = db.profiles
promotion_requests = db.promotion_requests
reaction_roles = db.reaction_roles
reminders = db.reminders
sessions = db.sessions
departments = db.departments

LOARegFormat = r"^(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?$"
loa_min = "1d"
loa_max = "1y"
loa_channel = 1454232138571448524
loa_role = 1454233756545323200

foundation_command = 1450297609515307134
site_command = 1450297617073442816