import os
import re
import sys
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError

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

async def resolve_group(client, group_link):
    """Resolves a group link or username to a Telegram entity."""
    group_link = group_link.strip()
    if not group_link:
        return None

    # Parse username from URL (t.me/groupname)
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', group_link)
    if match:
        target = match.group(1)
    elif group_link.startswith('@'):
        target = group_link[1:]
    else:
        target = group_link

    return await client.get_entity(target)

async def send_messages_from_account(session_name, group_targets, message, delay):
    """Sends the message to all target groups using a single account."""
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
            return

        me = await client.get_me()
        sender_name = f"{me.first_name} {me.last_name or ''}".strip()
        print(f"\n🔄 [{session_name}] Broadcasting as: {sender_name} (+{me.phone or 'None'})")

        for idx, group_link in enumerate(group_targets):
            try:
                print(f"   ⏳ Resolving group: {group_link}...")
                entity = await resolve_group(client, group_link)
                
                if entity:
                    await client.send_message(entity, message)
                    print(f"   ✅ Message sent to {group_link}!")
                else:
                    print(f"   ⚠️ Could not resolve: {group_link}")

            except FloodWaitError as e:
        print(f'   ⚠️ [{session_name}] Rate limited! Sleeping for {e.seconds} seconds...')
        await asyncio.sleep(e.seconds)
        return 'RETRY'
                print(f"   ⚠️ Rate limited. Need to wait {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(f"   ❌ Failed sending to {group_link}: {e}")

            # Apply delay between messages (if not the last message)
            if idx < len(group_targets) - 1:
                print(f"   🕒 Waiting {delay}s delay...")
                await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))

    except Exception as e:
        print(f"❌ [{session_name}] Connection error: {e}")
    finally:
        await client.disconnect()

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n======================================")
    print("      TELEGRAM GROUP BROADCASTER      ")
    print("======================================")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")

    # 1. Choose Accounts
    choices_raw = input("\nSelect sending accounts (e.g. 1, 2, 3): ").strip()
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

    selected_indices = list(set(selected_indices))
    if not selected_indices:
        print("❌ No valid accounts selected. Exiting.")
        return

    selected_sessions = [sessions[i] for i in selected_indices]
    print(f"Selected accounts: {', '.join(selected_sessions)}")

    # 2. Enter Message
    print("\nEnter your message. (To finish typing, press Ctrl+D on Mac/Linux or Ctrl+Z on Windows on a blank line):")
    lines = []
    try:
        for line in sys.stdin:
            lines.append(line)
    except KeyboardInterrupt:
        pass
    message = "".join(lines).strip()

    if not message:
        print("❌ Message content cannot be empty!")
        return

    # 3. Enter Group URLs
    groups_raw = input("\nEnter group links/usernames separated by comma (e.g., @group1, t.me/group2): ").strip()
    if not groups_raw:
        print("❌ No target groups specified!")
        return

    group_targets = [g.strip() for g in groups_raw.split(',') if g.strip()]
    if not group_targets:
        print("❌ No valid group targets parsed!")
        return

    # 4. Input Delay
    try:
        delay_raw = input("\nEnter delay between messages in seconds (default: 5): ").strip()
        delay = float(delay_raw) if delay_raw else 5.0
        if delay < 0:
            delay = 0.0
    except ValueError:
        print("⚠️ Invalid delay. Using default of 5 seconds.")
        delay = 5.0

    # Summary
    print("\n--- Broadcast summary ---")
    print(f"Sender accounts: {len(selected_sessions)}")
    print(f"Target groups:   {len(group_targets)}")
    print(f"Delay:           {delay}s")
    print(f"Message length:  {len(message)} chars")
    
    confirm = input("\nDo you want to start the broadcast now? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Broadcast cancelled.")
        return

    print("\nStarting broadcast process...")
    print("=" * 50)
    for session in selected_sessions:
        await send_messages_from_account(session, group_targets, message, delay)
        
    print("=" * 50)
    print("Broadcast finished!")

if __name__ == "__main__":
    asyncio.run(main())
