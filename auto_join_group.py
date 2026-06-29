import os
import re
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

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

def parse_group_link(url):
    """
    Parses a group/channel URL, username, or invite link.
    Returns (type, value) where type is 'username' or 'invite_hash'.
    """
    url = url.strip()
    
    # Private invite link: t.me/+hash or t.me/joinchat/hash
    invite_match = re.search(r'(?:t\.me|telegram\.me)/(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', url)
    if invite_match:
        return 'invite_hash', invite_match.group(1)
        
    # Public link: t.me/username or telegram.me/username
    public_match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if public_match:
        return 'username', public_match.group(1)
        
    # Standard username with @
    if url.startswith('@'):
        return 'username', url[1:]
        
    # Fallback to username
    return 'username', url

async def join_group(session_name, link_type, link_value):
    session_path = os.path.join(ACCOUNTS_DIR, session_name)
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
            print(f"❌ [{session_name}] Session is expired or unauthorized!")
            return False
            
        me = await client.get_me()
        name_str = f"{me.first_name} {me.last_name or ''}".strip()
        print(f"🔄 [{session_name}] Connecting as: {name_str} (+{me.phone or 'None'})")
        
        if link_type == 'invite_hash':
            await client(ImportChatInviteRequest(link_value))
            print(f"✅ [{session_name}] Joined private group successfully!")
        else:
            # Resolve public entity and join
            entity = await client.get_entity(link_value)
            await client(JoinChannelRequest(entity))
            print(f"✅ [{session_name}] Joined public group/channel successfully!")
            
        return True
    except Exception as e:
        print(f"❌ [{session_name}] Failed to join group: {e}")
        return False
    finally:
        await client.disconnect()

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n==============================")
    print("     TELEGRAM AUTO-JOINER     ")
    print("==============================")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")
        
    choices_raw = input("\nSelect accounts to join (e.g. 1, 2, 3): ").strip()
    if not choices_raw:
        print("No selection made. Exiting.")
        return

    selected_indices = []
    for part in choices_raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            idx = int(part)
            if 1 <= idx <= len(sessions):
                selected_indices.append(idx - 1)
            else:
                print(f"⚠️ Skipping invalid index: {idx}")
        except ValueError:
            print(f"⚠️ Skipping invalid input: '{part}'")

    selected_indices = list(set(selected_indices))  # Deduplicate
    if not selected_indices:
        print("❌ No valid accounts selected. Exiting.")
        return

    selected_sessions = [sessions[i] for i in selected_indices]
    print(f"\nSelected accounts: {', '.join(selected_sessions)}")

    group_url = input("\nEnter group/channel link or username (e.g., t.me/groupname or t.me/+invite_hash): ").strip()
    if not group_url:
        print("❌ Group link cannot be empty!")
        return

    link_type, link_value = parse_group_link(group_url)
    print(f"Parsed group link details -> Type: {link_type}, Value: {link_value}")
    
    print("\nStarting joining process...")
    print("-" * 50)
    for session in selected_sessions:
        await join_group(session, link_type, link_value)
        await asyncio.sleep(2)  # Delay between accounts to avoid Telegram API rate limits
        
    print("-" * 50)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
