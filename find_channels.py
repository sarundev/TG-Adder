import os
import csv
import asyncio
from telethon import TelegramClient, functions
from telethon.tl.types import Channel

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
    print("        FIND TELEGRAM CHANNELS        ")
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

    # 2. Input search parameters
    print("\nRegion is set to 'Cambodia Only'.")
    try:
        min_members = int(input("Enter minimum members (default 100000): ").strip() or "100000")
    except ValueError:
        min_members = 100000

        
    try:
        target_count = int(input("Enter target number of channels to find (default 100): ").strip() or "100")
    except ValueError:
        target_count = 100

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

        print(f"\nSearching for channels automatically for region 'Cambodia'...")
        print(f"Target: {target_count} channels with >= {min_members} members.\n")
        
        # Expanded list of Cambodian keywords to maximize results
        keywords_to_try = [
            "khmer", "cambodia", "phnom penh", "sabay", "news khmer", 
            "khmer news", "khmer update", "cambodia news", "siem reap",
            "khmer channel", "cambodia online", "shihanoukville", "khmer 24",
            "meas", "hang meas", "fresh news", "thmey thmey", "khmer song",
            "khmer music", "cambodia daily", "post khmer", "khmer times",
            "khmer funny", "khmer movie", "cambodia job", "phnom penh post",
            "khmer tech", "khmer sport", "khmer history", "khmer drama",
            "khmer health", "khmer crypto", "cambodia real estate",
            "kampong cham", "battambang", "kampot", "kandal", "takeo", 
            "khmer education", "cambodia travel", "khmer food", "cambodia life",
            "koh santepheap", "cnc news", "bayon tv", "ctn", "pnn", "khmer lotto",
            "khmer boxing", "kun khmer"
        ]
        
        found_channels = []
        seen_ids = set()
        
        for kw in keywords_to_try:
            if len(found_channels) >= target_count:
                break
                
            print(f"Searching query: '{kw}'...")
            try:
                result = await client(functions.contacts.SearchRequest(
                    q=kw,
                    limit=100
                ))
                
                for chat in result.chats:
                    if len(found_channels) >= target_count:
                        break
                        
                    # We are looking for channels (broadcast)
                    if getattr(chat, 'broadcast', False):
                        if chat.id in seen_ids:
                            continue
                        
                        seen_ids.add(chat.id)
                        
                        # Get full channel to get participant count
                        try:
                            full_channel = await client(functions.channels.GetFullChannelRequest(channel=chat))
                            count = full_channel.full_chat.participants_count
                            
                            if count is not None and count >= min_members:
                                username = chat.username or ""
                                link = f"https://t.me/{username}" if username else "Private/No Link"
                                title = chat.title or ""
                                print(f"✅ Found: {title} | {count} members | {link}")
                                
                                found_channels.append({
                                    'id': chat.id,
                                    'title': title,
                                    'username': username,
                                    'link': link,
                                    'members': count
                                })
                                
                        except Exception as e:
                            # Might be banned or rate limited
                            pass
                            
                # Sleep a bit to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Search error for '{kw}': {e}")
                
        print(f"\n✅ Finished searching. Found {len(found_channels)} channels matching criteria.")
        
        # 3. Save to file
        if found_channels:
            save_choice = input("\nDo you want to download the channels list to a file? (y/n): ").strip().lower()
            if save_choice == 'y':
                output_filename = f"channels_cambodia.csv"
                output_path = os.path.join(ACCOUNTS_DIR, output_filename)

                with open(output_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Channel ID', 'Title', 'Username', 'Link', 'Members Count'])
                    for c in found_channels:
                        writer.writerow([c['id'], c['title'], c['username'], c['link'], c['members']])

                print(f"\n✅ File downloaded successfully to: {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
