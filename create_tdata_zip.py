import asyncio
import os
import zipfile
import shutil
from telethon import TelegramClient
from opentele.td import TDesktop
from opentele.api import API, CreateNewSession

# Telegram Official API ID & Hash
API_ID = "2040"
API_HASH = "b18441a1ff607e10a989891a5462e627"

def zip_folder(folder_path, output_path):
    """Zips a folder completely."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # We want the folder inside the zip to be named "tdata"
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Ensure the root of the zip has the 'tdata' folder structure
                arcname = os.path.join("tdata", os.path.relpath(file_path, folder_path))
                zipf.write(file_path, arcname)

async def main():
    print("=== TELEGRAM TDATA CREATOR ===")
    phone = input("Enter the phone number (with country code, e.g. +123456789): ").strip()
    session_name = phone.replace("+", "")
    
    # 1. Connect and Send Code
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f"Requesting login code for {phone}...")
        await client.send_code_request(phone)
        
        # 2. User enters code
        code = input("Enter the Telegram code you received: ").strip()
        
        try:
            await client.sign_in(phone, code)
        except Exception as e:
            # If account doesn't exist, it might need signup
            if "SignUpRequiredError" in str(e):
                print("This is a new number! Registering...")
                first_name = input("Enter First Name for new account: ")
                await client.sign_up(code, first_name)
            else:
                print(f"Error signing in: {e}")
                return
                
    me = await client.get_me()
    print(f"\nSuccessfully logged in as: {me.first_name} (@{me.username})")
    
    # 3. Convert to TData using OpenTele
    print("\nConverting session to TData format...")
    tdata_folder = f"{session_name}_tdata"
    
    if os.path.exists(tdata_folder):
        shutil.rmtree(tdata_folder)
        
    tdesk = await TDesktop.FromTelethon(client, API.TelegramDesktop.Generate(), CreateNewSession)
    tdesk.SaveTData(tdata_folder)
    
    await client.disconnect()
    
    # 4. Zip it up just like the file you downloaded!
    zip_filename = f"{session_name}.zip"
    print(f"Creating ZIP file: {zip_filename} ...")
    
    # We want the structure inside the zip to be: 17825513530/tdata/key_datas
    # So we'll make a temporary wrapper folder
    wrapper_folder = session_name
    os.makedirs(wrapper_folder, exist_ok=True)
    shutil.move(tdata_folder, os.path.join(wrapper_folder, "tdata"))
    
    # Zip the wrapper folder
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(wrapper_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(wrapper_folder))
                zipf.write(file_path, arcname)
                
    # Clean up temporary folders
    shutil.rmtree(wrapper_folder)
    if os.path.exists(f"{session_name}.session"):
        os.remove(f"{session_name}.session")
        
    print(f"\nSUCCESS! Your account is saved as: {zip_filename}")
    print("You can now upload this zip file to your website to sell it!")

if __name__ == "__main__":
    asyncio.run(main())
