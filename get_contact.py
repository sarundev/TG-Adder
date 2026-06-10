import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.contacts import GetContactsRequest

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"
ACCOUNTS_DIR = "accounts"

def get_saved_sessions():
    """Returns a list of saved session names from accounts/ folder."""
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    
    sessions = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.endswith(".session"):
            sessions.append(f[:-8])
    return sorted(sessions)

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n==============================")
    print("   TELEGRAM CONTACT EXPORTER  ")
    print("==============================")
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
    client = TelegramClient(session_path, API_ID, API_HASH,
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
            return

        print("Fetching contact list...")
        result = await client(GetContactsRequest(hash=0))
        contacts = result.users
        
        if not contacts:
            print("No contacts found on this Telegram account.")
            return
            
        print("\n" + "="*60)
        print(f"👤 CONTACTS FOUND: {len(contacts)}")
        print("="*60)
        
        contact_records = []
        for idx, contact in enumerate(contacts, 1):
            first_name = contact.first_name or ""
            last_name = contact.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            username = f"@{contact.username}" if contact.username else "None"
            phone = f"+{contact.phone}" if contact.phone else "None"
            
            record = f"{idx:03d}. Name: {full_name:<25} | Username: {username:<20} | Phone: {phone:<16} | ID: {contact.id}"
            print(record)
            contact_records.append(record)
            
        print("="*60)
        
        save_choice = input("Do you want to save these contacts to a text file? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_filename = f"contact_{selected_session}.txt"
            output_path = os.path.join(ACCOUNTS_DIR, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Telegram Contacts Export\n")
                f.write(f"Account Session: {selected_session}\n")
                f.write(f"Total Contacts:  {len(contacts)}\n")
                f.write("="*80 + "\n\n")
                for record in contact_records:
                    f.write(record + "\n")
                    
            print(f"\n✅ Contacts saved successfully to: {output_path}")
            
    except Exception as e:
        print(f"❌ Error fetching contacts: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
