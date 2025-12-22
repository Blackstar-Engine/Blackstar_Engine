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
profiles = db.profiles
promotion_requests = db.promotion_requests
reaction_roles = db.reaction_roles
reminders = db.reminders
sessions = db.sessions
trainings = db.trainings