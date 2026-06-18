import asyncio
from telethon import TelegramClient

API_ID = 26500753
API_HASH = 81520134604

async def main():
    try:
        client = TelegramClient("test_login2.session", API_ID, API_HASH)
        await client.connect()
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
