import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User

import sys

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")

def get_saved_sessions():
    """Scans accounts/ directory and returns list of session names."""
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    
    sessions = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.endswith(".session"):
            # Strip the .session extension
            sessions.append(f[:-8])
    return sorted(sessions)

async def add_new_account():
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    print("\n--- Add/Login New Account ---")
    phone = input("Enter your phone number (with country code, e.g., +1234567890): ").strip()
    
    if not phone:
        print("Phone number cannot be empty!")
        return

    session_filename = phone.replace("+", "").replace(" ", "_")
    session_path = os.path.join(ACCOUNTS_DIR, session_filename)
    
    # Add realistic device details to prevent bans
    client = TelegramClient(
        session_path, 
        API_ID, 
        API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"Sending code to {phone}...")
            await client.send_code_request(phone)
            code = input("Enter the login code: ").strip()
            try:
                await client.sign_in(phone, code)
            except Exception as e:
                if "Two-step verification" in str(e) or "password" in str(e).lower():
                    password = input("2FA Password is required: ").strip()
                    await client.sign_in(password=password)
                else:
                    raise e
                    
        user = await client.get_me()
        print(f"\n🎉 Successfully logged in as {user.first_name}!")
        print(f"Session saved: {session_path}.session")
    except Exception as e:
        print(f"❌ Failed to login: {e}")
    finally:
        await client.disconnect()

async def view_account_info():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n--- Saved Telegram Accounts ---")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")
        
    try:
        choice_raw = input(f"Select an account (1-{len(sessions)}): ").strip()
        if not choice_raw:
            return
        choice = int(choice_raw)
        if choice < 1 or choice > len(sessions):
            print("Invalid selection.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    selected_session = sessions[choice - 1]
    session_path = os.path.join(ACCOUNTS_DIR, selected_session)
    
    print(f"\nConnecting to account: {selected_session}...")
    # Add realistic device details to prevent bans
    client = TelegramClient(
        session_path, 
        API_ID, 
        API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Session is expired or unauthorized!")
            # Offer to clean up
            cleanup = input("Do you want to delete this expired session file? (y/n): ").strip().lower()
            if cleanup == 'y':
                await client.disconnect()
                os.remove(session_path + ".session")
                print("Session file deleted.")
            return

        user = await client.get_me()
        print("\n" + "="*40)
        print("📂 TELEGRAM ACCOUNT INFO")
        print("="*40)
        print(f"User ID:    {user.id}")
        print(f"Name:       {user.first_name} {user.last_name or ''}")
        print(f"Username:   @{user.username if user.username else 'None'}")
        print(f"Phone:      +{user.phone if user.phone else 'None'}")
        print(f"Premium:    {'Yes' if user.premium else 'No'}")
        
        # Dialogs statistic
        print("Fetching chats & channels...")
        dialogs = await client.get_dialogs()
        
        personal_chats = 0
        groups = 0
        channels = 0
        
        for d in dialogs:
            if d.is_user:
                personal_chats += 1
            elif d.is_group:
                groups += 1
            elif d.is_channel:
                channels += 1
                
        print(f"Personal DM: {personal_chats}")
        print(f"Groups:      {groups}")
        print(f"Channels:    {channels}")
        print("="*40)
        
    except Exception as e:
        print(f"❌ Error retrieving account info: {e}")
    finally:
        await client.disconnect()

async def main():
    while True:
        print("\n==============================")
        print("   TELEGRAM MANAGER DASHBOARD ")
        print("==============================")
        print("1. Login / Add New Account")
        print("2. View Saved Account Info")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        if choice == "1":
            await add_new_account()
        elif choice == "2":
            await view_account_info()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, please enter 1, 2, or 3.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Program interrupted by user.")
    finally:
        os._exit(0)
