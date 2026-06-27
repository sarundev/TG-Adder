import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID", "22511037")
API_HASH = os.getenv("API_HASH", "8cd68731f82fbb9ebf9eb0ceceb9bd9f")

async def test_qr():
    client = TelegramClient("test_qr_session", api_id=int(API_ID), api_hash=API_HASH)
    await client.connect()
    try:
        qr = await client.qr_login()
        print("QR URL:", qr.url)
        
        # Test waiting for 2 seconds
        try:
            await asyncio.wait_for(qr.wait(), timeout=2.0)
            print("Done waiting, success?")
        except asyncio.TimeoutError:
            print("Timeout error, as expected (not scanned yet).")
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_qr())
