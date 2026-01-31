import os
import json
import gspread_asyncio
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

def get_creds():
    """
    Create Google credentials from environment variables.
    Handles multiple formats of GOOGLE_PRIVATE_KEY.
    """
    # Fetch the private key
    private_key = os.getenv("GOOGLE_PRIVATE_KEY")
    
    if not private_key:
        raise ValueError("GOOGLE_PRIVATE_KEY environment variable is not set")
    
    # Try multiple parsing strategies
    # Strategy 1: Replace literal \n string with actual newlines
    if '\\n' in private_key:
        private_key = private_key.replace('\\n', '\n')
    
    # Strategy 2: If it's JSON-encoded, decode it
    if private_key.startswith('"') and private_key.endswith('"'):
        try:
            private_key = json.loads(private_key)
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Remove any stray quotes at the beginning/end
    private_key = private_key.strip('"').strip("'")
    
    # Ensure it has the correct PEM format markers
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        raise ValueError("GOOGLE_PRIVATE_KEY does not start with '-----BEGIN PRIVATE KEY-----'")
    
    if not private_key.endswith('-----END PRIVATE KEY-----'):
        raise ValueError("GOOGLE_PRIVATE_KEY does not end with '-----END PRIVATE KEY-----'")
    
    # Build the credentials dictionary
    creds_dict = {
        "type": os.getenv("GOOGLE_TYPE", "service_account"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": private_key,
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL", 
                                                  "https://www.googleapis.com/oauth2/v1/certs"),
        "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
    }
    
    # Remove None values
    creds_dict = {k: v for k, v in creds_dict.items() if v is not None}
    
    # Create and return credentials
    try:
        return Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
    except Exception as e:
        print(f"Error creating credentials: {e}")
        print(f"Private key starts with: {private_key[:50]}...")
        print(f"Private key ends with: {private_key[-50:]}")
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