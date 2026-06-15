import os
import sys
import asyncio
import random
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User, MessageMediaPhoto, MessageMediaDocument
from telethon.tl.functions.messages import SendReactionRequest, GetDialogFiltersRequest
from telethon.tl.types import ReactionEmoji
from telethon.errors import FloodWaitError, UserPrivacyRestrictedError

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")

# --- Reaction Emojis Pool ---
REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "😍", "💯", "🙏", "⚡"]

# --- Friendly chat messages pool ---
CHAT_MESSAGES = [
    "Hey! How are you doing?",
    "What's up? Haven't talked in a while!",
    "Hey, hope you're having a great day! 😊",
    "Hi! Just checking in on you 🙏",
    "Hey! Hope everything's going well with you!",
    "What have you been up to lately?",
    "Hey man! Long time no chat 😄",
    "Hope you're doing well! 🙌",
    "Just wanted to say hi! How's life treating you?",
    "Hey! How's everything going? 😊",
]

def get_saved_sessions():
    """Returns a list of saved session names from accounts/ folder."""
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    sessions = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.endswith(".session"):
            sessions.append(f[:-8])
    return sorted(sessions)

def make_client(session_path):
    return TelegramClient(
        session_path, API_ID, API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )

# ─────────────────────────────────────────────
#  FEATURE 1: Auto React to group posts
# ─────────────────────────────────────────────
async def auto_react(client, session_name, groups, reactions_per_group=3, delay=10):
    """Reacts to recent posts in selected groups."""
    print(f"\n{'='*50}")
    print(f"⚡ [{session_name}] Starting Auto-React...")
    print(f"{'='*50}")

    total_reacted = 0

    for group in groups:
        group_name = getattr(group.entity, 'title', group.name)
        print(f"\n📣 Reacting in group: {group_name}")

        try:
            count = 0
            async for message in client.iter_messages(group.entity, limit=20):
                if count >= reactions_per_group:
                    break

                # Skip messages with no content or system messages
                if not message.text and not message.media:
                    continue
                if message.out:  # Skip own messages
                    continue

                try:
                    emoji = random.choice(REACTIONS)
                    await client(SendReactionRequest(
                        peer=group.entity,
                        msg_id=message.id,
                        reaction=[ReactionEmoji(emoticon=emoji)]
                    ))
                    print(f"   {emoji} Reacted to message ID {message.id} in '{group_name}'")
                    total_reacted += 1
                    count += 1

                    wait = random.uniform(delay * 0.8, delay * 1.5)
                    print(f"   🕒 Waiting {wait:.1f}s...")
                    await asyncio.sleep(wait)

                except FloodWaitError as e:
                    print(f"   ⚠️ Rate limit! Waiting {e.seconds}s...")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"   ❌ Failed to react: {e}")
                    continue

        except Exception as e:
            print(f"   ❌ Error reading group '{group_name}': {e}")
            continue

    print(f"\n✅ [{session_name}] Auto-React done! Total reactions: {total_reacted}")
    return total_reacted

# ─────────────────────────────────────────────
#  FEATURE 2: Auto Chat with contacts/friends
# ─────────────────────────────────────────────
async def auto_chat(client, session_name, contacts, message_count=3, delay=20):
    """Sends friendly messages to contacts/friends."""
    print(f"\n{'='*50}")
    print(f"💬 [{session_name}] Starting Auto-Chat...")
    print(f"{'='*50}")

    total_sent = 0
    sent_to = random.sample(contacts, min(message_count, len(contacts)))

    for contact in sent_to:
        name = getattr(contact.entity, 'first_name', None) or getattr(contact.entity, 'title', 'Friend')
        try:
            msg = random.choice(CHAT_MESSAGES)
            await client.send_message(contact.entity, msg)
            print(f"   ✅ Sent to {name}: \"{msg}\"")
            total_sent += 1

            wait = random.uniform(delay * 0.8, delay * 1.5)
            print(f"   🕒 Waiting {wait:.1f}s...")
            await asyncio.sleep(wait)

        except UserPrivacyRestrictedError:
            print(f"   ⚠️ {name} has privacy restrictions, skipping...")
        except FloodWaitError as e:
            print(f"   ⚠️ Rate limit! Waiting {e.seconds}s...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"   ❌ Failed to message {name}: {e}")
            continue

    print(f"\n✅ [{session_name}] Auto-Chat done! Messages sent: {total_sent}")
    return total_sent

# ─────────────────────────────────────────────
#  FEATURE 3: Combined Warm Session
# ─────────────────────────────────────────────
async def warm_session(session_name, do_react=True, do_chat=True,
                        react_groups=None, chat_contacts=None,
                        reactions_per_group=3, messages_to_send=3,
                        react_delay=10, chat_delay=20):
    """Runs a full warming session for one account."""
    session_path = os.path.join(ACCOUNTS_DIR, session_name)
    client = make_client(session_path)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"❌ [{session_name}] Session expired or unauthorized. Skipping.")
            return

        me = await client.get_me()
        print(f"\n🔄 Warming account: {me.first_name} (+{me.phone or 'N/A'})")

        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        contacts = [d for d in dialogs if d.is_user and not getattr(d.entity, 'bot', False)]

        # Filter selected groups if specified
        if react_groups:
            selected_groups = [g for g in groups if g.name in react_groups or str(g.id) in react_groups]
        else:
            # Pick random groups if none specified
            selected_groups = random.sample(groups, min(3, len(groups))) if groups else []

        if do_react:
            if not selected_groups:
                print(f"⚠️ [{session_name}] No groups available to react in.")
            else:
                await auto_react(client, session_name, selected_groups,
                                 reactions_per_group=reactions_per_group,
                                 delay=react_delay)

        if do_chat:
            if not contacts:
                print(f"⚠️ [{session_name}] No contacts/friends to chat with.")
            else:
                await auto_chat(client, session_name, contacts,
                                message_count=messages_to_send,
                                delay=chat_delay)

    except Exception as e:
        print(f"❌ [{session_name}] Warming error: {e}")
    finally:
        await client.disconnect()

# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\n❌ No saved accounts found in accounts/ directory.")
        return

    print("\n" + "=" * 55)
    print("   🔥 TELEGRAM ACCOUNT WARMER                     ")
    print("   Keeps accounts active to avoid restrictions     ")
    print("=" * 55)

    # Select accounts
    print("\n📋 Available Accounts:")
    for idx, session in enumerate(sessions, 1):
        print(f"  {idx}. {session}")

    choices_raw = input("\nSelect accounts to warm (e.g. 1,2,3 or 'all'): ").strip()

    if choices_raw.lower() == 'all':
        selected_sessions = sessions
    else:
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
                    print(f"⚠️ Invalid index: {idx}")
            except ValueError:
                print(f"⚠️ Invalid input: '{part}'")

        selected_indices = list(set(selected_indices))
        if not selected_indices:
            print("❌ No valid accounts selected. Exiting.")
            return

        selected_sessions = [sessions[i] for i in selected_indices]

    print(f"\n✅ Selected: {', '.join(selected_sessions)}")

    # Select features
    print("\n🛠️  What do you want to do?")
    print("  1. Auto React only (react to group posts)")
    print("  2. Auto Chat only  (message friends/contacts)")
    print("  3. Both React + Chat (recommended)")

    mode = input("\nSelect mode (1/2/3, default: 3): ").strip() or "3"

    do_react = mode in ("1", "3")
    do_chat  = mode in ("2", "3")

    # Configure settings
    print("\n⚙️  Settings:")

    reactions_per_group = 3
    react_delay = 10
    if do_react:
        try:
            r = input("  Reactions per group (default: 3): ").strip()
            reactions_per_group = int(r) if r else 3
        except ValueError:
            reactions_per_group = 3

        try:
            d = input("  Delay between reactions in seconds (default: 10): ").strip()
            react_delay = float(d) if d else 10.0
        except ValueError:
            react_delay = 10.0

    messages_to_send = 3
    chat_delay = 20
    if do_chat:
        try:
            m = input("  Messages to send per account (default: 3): ").strip()
            messages_to_send = int(m) if m else 3
        except ValueError:
            messages_to_send = 3

        try:
            d = input("  Delay between messages in seconds (default: 20): ").strip()
            chat_delay = float(d) if d else 20.0
        except ValueError:
            chat_delay = 20.0

    # Loop mode
    loop_mode = input("\n🔁 Enable loop mode? Runs continuously on a timer (y/n, default: n): ").strip().lower()
    loop_interval = 0
    if loop_mode == 'y':
        try:
            h = input("  Run every how many hours? (default: 6): ").strip()
            loop_interval = float(h) * 3600 if h else 6 * 3600
        except ValueError:
            loop_interval = 6 * 3600

    print("\n" + "=" * 55)
    print(f"🚀 Starting warming for {len(selected_sessions)} account(s)...")
    print("   Press Ctrl+C to stop at any time.")
    print("=" * 55)

    run_count = 0
    while True:
        run_count += 1
        if loop_interval > 0:
            print(f"\n🔁 === WARM CYCLE #{run_count} ===")

        for session in selected_sessions:
            await warm_session(
                session,
                do_react=do_react,
                do_chat=do_chat,
                reactions_per_group=reactions_per_group,
                messages_to_send=messages_to_send,
                react_delay=react_delay,
                chat_delay=chat_delay
            )
            if len(selected_sessions) > 1:
                between_delay = random.uniform(30, 60)
                print(f"\n⏳ Switching to next account in {between_delay:.0f}s...")
                await asyncio.sleep(between_delay)

        print("\n✅ All accounts warmed successfully!")

        if loop_interval > 0:
            hours = loop_interval / 3600
            print(f"\n😴 Sleeping for {hours:.1f} hours until next cycle...")
            print(f"   (Press Ctrl+C to stop)")
            await asyncio.sleep(loop_interval)
        else:
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Warming stopped by user.")
    finally:
        os._exit(0)
