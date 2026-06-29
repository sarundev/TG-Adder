from telethon import TelegramClient
API_ID = 26500753
API_HASH = "815cc20b134604fbaf8a156ceebba235"

client = TelegramClient("test", API_ID, API_HASH)
print(f"api_id={client.api_id} ({type(client.api_id)})")
print(f"api_hash={client.api_hash} ({type(client.api_hash)})")
