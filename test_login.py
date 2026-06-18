import asyncio
from telethon import TelegramClient

API_ID = 26500753
API_HASH = "815cc20b134604fbaf8a156ceebba235"

async def main():
    try:
        client = TelegramClient("test_login.session", API_ID, API_HASH,
            device_model="iPhone 13 Pro Max",
            system_version="15.5",
            app_version="8.7.1",
            lang_code="en",
            system_lang_code="en"
        )
        await client.connect()
        print("Connected.")
        
        # Test send_code_request with a fake number
        phone = "+85512345678"
        print(f"Sending code to {phone}")
        await client.send_code_request(phone)
        print("Code sent.")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        await client.disconnect()

asyncio.run(main())
