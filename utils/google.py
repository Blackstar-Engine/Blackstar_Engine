import gspread_asyncio
from google.oauth2.service_account import Credentials

def get_creds():
    return Credentials.from_service_account_file(
        '/home/tristyn/Blackstar_Corp_Bot/utils/credentials.json',
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
        
        # Loop through worksheets to find the one matching the GID
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

    async def fetch_row(self, row_num):
        if not self.sheet: return []
        return await self.sheet.row_values(row_num)
