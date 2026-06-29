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
SMS_API_KEY = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MTMzNDEzNzgsImlhdCI6MTc4MTgwNTM3OCwicmF5IjoiNTZhZGViMDQ0NDAxMmY3MDQ0OTk4YmYwYzE5OTE3MTEiLCJzdWIiOjQyMjc5Nzd9.zFgy1BMMXLllXDK9vJ2V_AItgIOo7IwZgji4tmPPbqYb8vLaXhsQBNlhakTCEffQU3XCiUnH2sxtdx0oPigx1tWcuh-OCLB1GQ-i4B-CBJOAYgNndW8P-gz558K1yovYjOPFIqsHRxoQ8JdiypdOM_K_t0TFonIJ126K8vTgh5313Ku8TffKsGT_KfKyvvXz5i4Jw6-Yfnf_IVJPENDzzMQJ_3Zk8KSHlc6CXtj9EjF8QNizkfI_Soffx4ZneTCn7WpGd7eVgAhjkWkgebopeIp0j-aFfZ4brhN9xkmxFv_nggEBwb2EIsw4K3A0ZFjgCjsh_LMTjB9axwue_l15zw"
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

async def get_phone_number(country="cambodia", operator="any"):
    """Fetch a phone number from the SMS API."""
    print("Requesting phone number...")
    # Example using 5sim.net API
    headers = {"Authorization": f"Bearer {SMS_API_KEY}", "Accept": "application/json"}
    url = f"{SMS_PROVIDER_URL}/buy/activation/{country}/{operator}/telegram"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error buying number: {response.text}")
        return None, None
        
    try:
        data = response.json()
    except Exception:
        print(f"Failed to buy number. API Response: {response.text.strip()}")
        if "no free phones" in response.text:
            print("Tip: 5sim has no phones left for this country. Try changing 'russia' to another country in the code.")
        elif "not enough" in response.text:
            print("Tip: Telegram numbers usually cost 15-30 rubles. Your 5sim balance is only 5 rubles. Please add more funds!")
        return None, None
        
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
    client = TelegramClient(
        session_name, 
        api_id=API_ID, 
        api_hash=API_HASH,
        system_version="4.1.6 API",
        device_model="Desktop",
        app_version="4.2.4"
    )
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
        import traceback
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
    finally:
        await client.disconnect()
        # Clean up temporary files
        if os.path.exists(f"{session_name}.session"):
            os.remove(f"{session_name}.session")
        if os.path.exists(f"{session_name}_tdata"):
            shutil.rmtree(f"{session_name}_tdata")

if __name__ == "__main__":
    asyncio.run(create_account())
