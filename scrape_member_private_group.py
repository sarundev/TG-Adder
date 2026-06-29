import os
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

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n======================================")
    print("      TELEGRAM PRIVATE GROUP SCRAPER  ")
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

        print("Fetching your group list...")
        dialogs = await client.get_dialogs()
        
        # Filter only group dialogs
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        
        if not groups:
            print("❌ This Telegram account is not joined to any groups.")
            return

        print("\n--- Available Joined Groups & Channels ---")
        for idx, g in enumerate(groups, 1):
            print(f"{idx:02d}. {g.name:<30} | ID: {g.id}")

        # 2. Select Group
        try:
            grp_choice_raw = input(f"\nSelect group to scrape (1-{len(groups)}): ").strip()
            if not grp_choice_raw:
                return
            grp_choice = int(grp_choice_raw)
            if grp_choice < 1 or grp_choice > len(groups):
                print("Invalid group selection.")
                return
        except ValueError:
            print("Please enter a valid number.")
            return

        selected_group = groups[grp_choice - 1]
        group_entity = selected_group.entity
        group_title = selected_group.name
        
        print(f"\nStarting member scrape for: '{group_title}'... (This might take a moment depending on the group size)")
        
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
            print("No members fetched. Ensure you have permissions to view members in this private group.")
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
            # Create a clean safe filename
            safe_title = "".join([c if c.isalnum() else "_" for c in group_title])
            output_filename = f"members_private_{safe_title}.csv"
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
