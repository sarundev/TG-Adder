import os
import re
import csv
import asyncio
from telethon import TelegramClient

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

def parse_input_link(url):
    """
    Extracts the identifier from public links, usernames, or private hashes.
    Returns (link_type, identifier)
    """
    url = url.strip()
    
    # Private invite link: t.me/+hash or t.me/joinchat/hash
    invite_match = re.search(r'(?:t\.me|telegram\.me)/(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', url)
    if invite_match:
        return 'private_hash', invite_match.group(1)
        
    # Public link: t.me/username
    public_match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if public_match:
        return 'public_username', public_match.group(1)
        
    # Standard username with @
    if url.startswith('@'):
        return 'public_username', url[1:]
        
    # Fallback to username
    return 'public_username', url

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n======================================")
    print("      TELEGRAM PUBLIC/PRIVATE SCRAPER ")
    print("======================================")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")

    # 1. Choose Account
    try:
        choice_raw = input(f"\nSelect an account (1-{len(sessions)}): ").strip()
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

    # 2. Input Group URL
    group_url = input("\nEnter group link, username, or invite link (e.g. t.me/groupname or t.me/+invite_hash): ").strip()
    if not group_url:
        print("❌ Group identifier cannot be empty!")
        return

    link_type, identifier = parse_input_link(group_url)
    
    print(f"\nConnecting using account: {selected_session}...")
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

        group_entity = None
        
        # If it is a private invite link, try to find a matching chat in user's dialogs.
        # (The user must already have joined the group to scrape it).
        if link_type == 'private_hash':
            print("🔍 Private link detected. Searching your joined chats/groups to find a match...")
            dialogs = await client.get_dialogs()
            
            # Since invite hash is not directly exposed in dialog entities,
            # we ask the user for a keyword to help locate the correct group from their list
            print("\nBecause this is a private group, we need to match it against your joined chats.")
            keyword = input("Enter a keyword or name of the private group to search: ").strip().lower()
            
            matches = []
            for d in dialogs:
                if (d.is_group or d.is_channel) and keyword in d.name.lower():
                    matches.append(d)
                    
            if not matches:
                print("❌ No matching group found in your joined chat list. Make sure you have joined the group!")
                return
                
            if len(matches) == 1:
                group_entity = matches[0].entity
                print(f"👉 Found match: {matches[0].name}")
            else:
                print("\nMultiple matching groups found:")
                for idx, match in enumerate(matches, 1):
                    print(f"{idx}. {match.name} (ID: {match.id})")
                sel = int(input(f"Select group (1-{len(matches)}): ").strip())
                group_entity = matches[sel - 1].entity
        else:
            # Public Group resolution
            try:
                print(f"Resolving group entity for @{identifier}...")
                group_entity = await client.get_entity(identifier)
            except Exception:
                # If direct resolution fails, search user dialogs as fallback
                print("🔍 Could not resolve public identifier directly. Searching your joined chats...")
                dialogs = await client.get_dialogs()
                for d in dialogs:
                    if (d.is_group or d.is_channel) and (identifier.lower() in d.name.lower() or (getattr(d.entity, 'username', '') and identifier.lower() == d.entity.username.lower())):
                        group_entity = d.entity
                        print(f"👉 Found match in your chats: {d.name}")
                        break
                        
        if not group_entity:
            print("❌ Could not find or resolve the group entity. Please make sure the link is correct and you have joined the group.")
            return

        print("\nStarting member scrape... (This might take a moment depending on the group size)")
        
        members = []
        async for user in client.iter_participants(group_entity):
            members.append({
                'id': user.id,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'phone': user.phone or '',
                'is_bot': 'Yes' if user.bot else 'No'
            })

        print(f"\n✅ Successfully scraped {len(members)} members!")
        if not members:
            print("No members fetched. Ensure you have permissions to view group members.")
            return

        # Print quick preview
        print("\n--- Preview (First 5 members) ---")
        for m in members[:5]:
            fullname = f"{m['first_name']} {m['last_name']}".strip()
            username = f"@{m['username']}" if m['username'] else "None"
            print(f"ID: {m['id']} | Name: {fullname:<20} | Username: {username}")
        if len(members) > 5:
            print(f"... and {len(members) - 5} more.")

        # 3. Prompt to save
        save_choice = input("\nDo you want to save the scraped members list? (y/n): ").strip().lower()
        if save_choice == 'y':
            # Safe filename generation
            safe_title = getattr(group_entity, 'title', identifier)
            safe_filename = "".join([c if c.isalnum() else "_" for c in safe_title])
            output_filename = f"members_{safe_filename}.csv"
            output_path = os.path.join(ACCOUNTS_DIR, output_filename)

            with open(output_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['User ID', 'Username', 'First Name', 'Last Name', 'Phone', 'Is Bot'])
                for m in members:
                    writer.writerow([m['id'], m['username'], m['first_name'], m['last_name'], m['phone'], m['is_bot']])

            print(f"\n✅ Member list saved successfully to: {output_path}")

    except Exception as e:
        print(f"❌ Error scraping group: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
