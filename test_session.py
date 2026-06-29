import asyncio
from telethon import TelegramClient

API_ID = 26563604
API_HASH = "8095d3e35a09b4009dd57b54a2db6591"

async def main():
    for phone in ["85517629584", "855716229006"]:
        client = TelegramClient(f"accounts/{phone}", api_id=API_ID, api_hash=API_HASH)
        await client.connect()
        auth = await client.is_user_authorized()
        print(f"{phone}: {auth}")
        await client.disconnect()

asyncio.run(main())
