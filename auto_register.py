import asyncio
import time
import os
import zipfile
import shutil
import random
import requests
from telethon import TelegramClient
from opentele.td import TDesktop
from opentele.api import API, CreateNewSession

# --- CONFIGURATION ---
API_ID = 2040  # Default official API ID
API_HASH = "b18441a1ff607e10a989891a5462e627"

# Choose your SMS provider. For this example, we'll use 5sim.net
# You can change this to smshub, sms-activate, etc.
SMS_API_KEY = "YOUR_SMS_API_KEY_HERE"
SMS_PROVIDER_URL = "https://5sim.net/v1/user" # Example for 5sim

FIRST_NAMES = ["John", "David", "Michael", "Sarah", "Emma", "Anna", "Lisa", "James", "Robert"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

def zip_folder(folder_path, output_path):
    """Zips a folder completely."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, arcname)

async def get_phone_number(country="russia", operator="any"):
    """Fetch a phone number from the SMS API."""
    print("Requesting phone number...")
    # Example using 5sim.net API
    headers = {"Authorization": f"Bearer {SMS_API_KEY}", "Accept": "application/json"}
    url = f"{SMS_PROVIDER_URL}/buy/activation/{country}/{operator}/telegram"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error buying number: {response.text}")
        return None, None
        
    data = response.json()
    order_id = data.get("id")
    phone = data.get("phone")
    print(f"Got phone number: {phone} (Order ID: {order_id})")
    return phone, order_id

async def get_sms_code(order_id, retries=30, delay=5):
    """Poll the SMS API for the verification code."""
    print("Waiting for SMS code from Telegram...")
    headers = {"Authorization": f"Bearer {SMS_API_KEY}", "Accept": "application/json"}
    url = f"{SMS_PROVIDER_URL}/check/{order_id}"
    
    for i in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "RECEIVED":
                sms_list = data.get("sms", [])
                if sms_list:
                    code = sms_list[0].get("code")
                    print(f"Received Code: {code}")
                    return code
        await asyncio.sleep(delay)
        print(f"Still waiting... ({i+1}/{retries})")
    print("Timeout waiting for SMS code.")
    return None

async def create_account():
    # 1. Get phone number
    if SMS_API_KEY == "YOUR_SMS_API_KEY_HERE":
        print("Please set your SMS_API_KEY in the script first!")
        return
        
    phone, order_id = await get_phone_number()
    if not phone:
        return

    # 2. Start Telethon
    session_name = phone.replace("+", "")
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    
    try:
        # 3. Request Code from Telegram
        print(f"Sending code request to {phone}...")
        send_code = await client.send_code_request(phone)
        phone_code_hash = send_code.phone_code_hash
        
        # 4. Get code from SMS API
        code = await get_sms_code(order_id)
        if not code:
            await client.disconnect()
            return
            
        # 5. Sign up
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        print(f"Signing up as {first_name} {last_name}...")
        
        await client.sign_up(code, first_name, last_name)
        
        # Get My Info
        me = await client.get_me()
        print(f"Success! Account created: {me.phone}")
        
        # 6. Convert to TData using opentele
        print("Converting to TData format...")
        tdata_folder = f"{session_name}_tdata"
        if os.path.exists(tdata_folder):
            shutil.rmtree(tdata_folder)
            
        tdesk = await TDesktop.FromTelethon(client, API.TelegramDesktop.Generate(), CreateNewSession)
        tdesk.SaveTData(tdata_folder)
        
        # 7. Zip the TData folder
        zip_filename = f"{session_name}.zip"
        print(f"Zipping into {zip_filename}...")
        zip_folder(tdata_folder, zip_filename)
        
        print(f"Done! Your new account is ready in {zip_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await client.disconnect()
        # Clean up temporary files
        if os.path.exists(f"{session_name}.session"):
            os.remove(f"{session_name}.session")
        if os.path.exists(f"{session_name}_tdata"):
            shutil.rmtree(f"{session_name}_tdata")

if __name__ == "__main__":
    asyncio.run(create_account())
