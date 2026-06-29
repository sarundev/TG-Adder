import asyncio
from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession

async def main():
    tdata_folder = "/Users/bongrun/Documents/tdata"
    api = API.TelegramDesktop.Generate()
    
    # Load the tdata
    tdesk = TDesktop(tdata_folder)
    print(f"Loaded TDesktop. Has sessions: {tdesk.isLoaded()}")
    
    # Create Telethon client
    client = await tdesk.ToTelethon("tdata_test.session", UseCurrentSession, api)
    
    await client.connect()
    user = await client.get_me()
    print("Logged in as:", user.first_name, user.phone)
    await client.disconnect()

asyncio.run(main())
