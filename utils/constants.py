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
loa_channel = 1412244838660968590
loa_role = 1418067647177691156

foundation_command = 1413208971304636597
site_command = 1422416268585341049
high_command = 1413226553982320713
central_command = 1413226456968069180
ia_id = 1413193754013073459
wolf_id = 1371489554279825439