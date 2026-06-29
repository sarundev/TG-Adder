import asyncio
from telethon import TelegramClient

async def test():
    client = TelegramClient("test_phone_2040", api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627")
    await client.connect()
    try:
        await client.send_code_request("+1234567890")
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test())
