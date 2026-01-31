import os
import gspread_asyncio
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

def get_creds():
    """
    Create Google credentials from a JSON file.
    Expects credentials at ~/home/credentials.json by default.
    """
    # Path to the credentials file (expanduser handles ~ expansion)
    creds_path = os.path.expanduser(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "~/home/credentials.json")
    )
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Google credentials file not found at: {creds_path}\n"
            f"Please ensure credentials.json is at ~/home/credentials.json\n"
            f"or set GOOGLE_APPLICATION_CREDENTIALS environment variable"
        )
    
    try:
        return Credentials.from_service_account_file(
            creds_path,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
    except Exception as e:
        print(f"❌ Error loading credentials from {creds_path}: {e}")
        raise


class GSheet:
    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.sheet = None

    async def connect(self, gid: int):
        """Connects to the spreadsheet and finds the specific tab by GID."""
        try:
            client = await self.agcm.authorize()
            spreadsheet = await client.open_by_key("1DnB_gri9nkZFXAe96KNCtbV2gnrYI4IxFgFR26V4yo0")
            
            worksheets = await spreadsheet.worksheets()
            found = False
            for ws in worksheets:
                if ws.id == gid:
                    self.sheet = ws
                    found = True
                    break
            
            if not found:
                print(f"⚠️ Warning: Worksheet with GID {gid} not found.")
                self.sheet = None
            else:
                print(f"✅ Successfully connected to worksheet GID {gid}")
                
        except Exception as e:
            print(f"❌ Error connecting to GID {gid}: {e}")
            self.sheet = None

    async def fetch_all_data(self):
        """Fetches all rows from the connected worksheet."""
        if not self.sheet:
            print("⚠️ No sheet connected")
            return []
        
        try:
            data = await self.sheet.get_all_values()
            print(f"✅ Fetched {len(data)} rows")
            return data
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return []