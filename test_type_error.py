import asyncio
from telethon import TelegramClient
import os

API_ID = 26500753
API_HASH = "815cc20b134604fbaf8a156ceebba235"
ACCOUNTS_DIR = "accounts"

async def test_login():
    phone = "+855716229006"
    session_filename = phone.replace("+", "").replace(" ", "_")
    session_path = os.path.join(ACCOUNTS_DIR, session_filename)
    
    print(f"session_path: {session_path}")
    print(f"API_ID: {API_ID} type: {type(API_ID)}")
    print(f"API_HASH: {API_HASH} type: {type(API_HASH)}")
    print(f"phone: {phone} type: {type(phone)}")

    try:
        client = TelegramClient(session_path, API_ID, API_HASH,
            device_model="iPhone 13 Pro Max",
            system_version="15.5",
            app_version="8.7.1",
            lang_code="en",
            system_lang_code="en"
        )
        print("TelegramClient initialized.")
        await client.connect()
        print("Connected.")
        
        await client.send_code_request(phone)
        print("Code sent.")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test_login())
