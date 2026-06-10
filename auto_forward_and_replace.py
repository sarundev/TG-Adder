import os
import re
import asyncio
from telethon import TelegramClient, events

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

    print("\n=============================================")
    print("      TELEGRAM AUTO-FORWARD & LINK REPLACER  ")
    print("=============================================")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")

    # 1. Choose Account
    try:
        choice_raw = input("\nSelect account to run the bot on (1, 2, 3...): ").strip()
        choice = int(choice_raw)
        if choice < 1 or choice > len(sessions):
            print("Invalid selection.")
            return
    except ValueError:
        print("Invalid input.")
        return

    session_name = sessions[choice - 1]
    session_path = os.path.join(ACCOUNTS_DIR, session_name)

    print(f"\nConnecting with account '{session_name}'...")
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

    await client.connect()
    if not await client.is_user_authorized():
        print(f"❌ Session '{session_name}' is unauthorized! Log in first.")
        await client.disconnect()
        return

    print("Fetching your groups and channels...")
    dialogs = await client.get_dialogs()
    chats = [d for d in dialogs if d.is_group or d.is_channel]

    if not chats:
        print("❌ This Telegram account is not joined to any groups or channels!")
        await client.disconnect()
        return

    print("\n--- Available Chats (Source & Target) ---")
    for idx, c in enumerate(chats, 1):
        print(f"{idx:02d}. {c.name:<30} | ID: {c.id}")

    # 2. Select Source
    try:
        src_choice = int(input(f"\nSelect SOURCE Chat to listen for new messages (1-{len(chats)}): ").strip())
        source_chat = chats[src_choice - 1]
    except (ValueError, IndexError):
        print("Invalid source selection.")
        await client.disconnect()
        return

    # 3. Select Target
    try:
        tgt_choice = int(input(f"Select TARGET Chat to forward modified messages to (1-{len(chats)}): ").strip())
        target_chat = chats[tgt_choice - 1]
    except (ValueError, IndexError):
        print("Invalid target selection.")
        await client.disconnect()
        return

    # 4. Replacement Link
    my_link = input("\nEnter YOUR Telegram link/username to replace the original links with (e.g. @MyChannel or t.me/MyChannel): ").strip()
    if not my_link:
        print("Replacement link cannot be empty!")
        await client.disconnect()
        return

    print("\n" + "=" * 60)
    print(f"Bot is now running and listening on: {source_chat.name}")
    print(f"Forwarding messages to: {target_chat.name}")
    print(f"Replacing all t.me links and @usernames with: {my_link}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    # Event handler for new messages in the source chat
    @client.on(events.NewMessage(chats=[source_chat.id]))
    async def handler(event):
        # We only want text messages or media with captions
        original_text = event.message.message
        
        if not original_text and not event.message.media:
            return # empty message
            
        modified_text = original_text if original_text else ""

        # Custom handler to process URLs
        def url_handler(match):
            url = match.group(0).lower()
            # If it's a Telegram link, replace it with my_link
            if 't.me' in url or 'telegram.me' in url:
                return my_link
            # Otherwise, it's an external link (like YouTube), so we remove it
            return ""

        # 1. Match and process all URLs (http, https, www, t.me)
        modified_text = re.sub(r'(?:https?://|www\.)[^\s]+|\b(?:t\.me|telegram\.me)/[a-zA-Z0-9_]+', url_handler, modified_text)
        
        # 2. Replace @ usernames with my_link
        modified_text = re.sub(r'@[a-zA-Z0-9_]+', my_link, modified_text)

        try:
            # If the message has media, we need to send the media with the modified caption
            if event.message.media:
                await client.send_message(target_chat.id, modified_text, file=event.message.media)
            else:
                await client.send_message(target_chat.id, modified_text)
                
            print(f"✅ Forwarded a message and replaced links.")
        except Exception as e:
            print(f"❌ Failed to forward message: {e}")

    # Keep the script running
    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        print("\nStopping bot...")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
