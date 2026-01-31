import os
import gspread_asyncio
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

def get_creds():
    # 1. Fetch the Private Key and fix newlines
    # .env files often escape newlines as string literals ('\n'), 
    # but Google needs actual newlines.
    private_key = os.getenv("GOOGLE_PRIVATE_KEY")
    if private_key:
        private_key = private_key.replace('\\n', '\n')

    # 2. Build the dictionary manually
    creds_dict = {
        "type": os.getenv("GOOGLE_TYPE"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": private_key,
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
        "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
    }

    # 3. Create credentials from the dictionary info
    return Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets', 
            'https://www.googleapis.com/auth/drive' 
        ]
    )

class GSheet:
    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.sheet = None

    async def connect(self, gid: int):
        """Connects to the spreadsheet and finds the specific tab by GID."""
        client = await self.agcm.authorize()
        # Ensure this ID is correct for your main spreadsheet
        spreadsheet = await client.open_by_key("1DnB_gri9nkZFXAe96KNCtbV2gnrYI4IxFgFR26V4yo0")
        
        worksheets = await spreadsheet.worksheets()
        found = False
        for ws in worksheets:
            if ws.id == gid:
                self.sheet = ws
                found = True
                break
        
        if not found:
            print(f"Warning: Worksheet with GID {gid} not found.")
            self.sheet = None

    async def fetch_all_data(self):
        """Fetches all rows from the connected worksheet."""
        if not self.sheet:
            return []
        return await self.sheet.get_all_values()