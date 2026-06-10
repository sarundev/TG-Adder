import os
import random
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.errors import (
    FloodWaitError, 
    UserPrivacyRestrictedError, 
    UserAlreadyParticipantError,
    UserIdInvalidError,
    PeerFloodError
)

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

async def add_single_user(client, target_entity, user_entity, session_name):
    """Invites a single resolved user entity to a target channel/group entity."""
    user_label = f"@{user_entity.username}" if user_entity.username else f"ID {user_entity.id}"
    try:
        if isinstance(target_entity, Channel):
            # Handles both Broadcast Channels and Megagroups/Supergroups
            await client(InviteToChannelRequest(target_entity, [user_entity]))
        elif isinstance(target_entity, Chat):
            # Handles legacy Chat groups
            await client(AddChatUserRequest(chat_id=target_entity.id, user_id=user_entity, fwd_limit=0))
        else:
            raise ValueError(f"Unsupported group/channel entity type: {type(target_entity)}")
            
        print(f"   ✅ [{session_name}] Successfully added: {user_label}")
        return True
    except UserPrivacyRestrictedError:
        print(f"   ⚠️ [{session_name}] Privacy settings restricted adding: {user_label}")
    except UserAlreadyParticipantError:
        print(f"   ℹ️ [{session_name}] Already in channel/group: {user_label}")
    except UserIdInvalidError:
        print(f"   ❌ [{session_name}] Invalid user identifier: {user_label}")
    except PeerFloodError:
        print(f"   ❌ [{session_name}] Account has been flagged/restricted by Telegram (PeerFloodError)!")
        return "RESTRICTED"
    except FloodWaitError as e:
        print(f"   ⚠️ [{session_name}] Rate limited! Must wait {e.seconds}s.")
        return e.seconds
    except Exception as e:
        print(f"   ❌ [{session_name}] Failed to add {user_label}: {e}")
    return False

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n=============================================")
    print("   TELEGRAM CHANNEL/GROUP AUTO-INVITER       ")
    print("=============================================")
    for idx, session in enumerate(sessions, 1):
        print(f"{idx}. {session}")

    # 1. Choose Accounts
    choices_raw = input("\nSelect inviting accounts (e.g. 1, 2, 3): ").strip()
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

    # Use the first selected account to scrape the group/channel list
    primary_session = selected_sessions[0]
    primary_path = os.path.join(ACCOUNTS_DIR, primary_session)
    
    print(f"\nConnecting with primary account '{primary_session}' to fetch joined chats/channels...")
    primary_client = TelegramClient(primary_path, API_ID, API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )
    
    try:
        await primary_client.connect()
        if not await primary_client.is_user_authorized():
            print(f"❌ Primary session '{primary_session}' is unauthorized! Log in first.")
            return

        dialogs = await primary_client.get_dialogs()
        
        # Include both standard Chat groups and Channels (which cover Supergroups and Channels)
        chats = [d for d in dialogs if d.is_group or d.is_channel]
        
        if not chats:
            print("❌ This Telegram account is not joined to any groups or channels!")
            return

        print("\n--- Available Joined Groups & Channels ---")
        for idx, c in enumerate(chats, 1):
            chat_type = "Channel" if c.is_channel else "Group"
            print(f"{idx:02d}. [{chat_type:<7}] {c.name:<30} | ID: {c.id}")

        # 2. Select Source Channel/Group
        try:
            src_choice = int(input(f"\nSelect SOURCE (to scrape members from) (1-{len(chats)}): ").strip())
            if src_choice < 1 or src_choice > len(chats):
                print("Invalid source selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
        
        source_chat = chats[src_choice - 1]
        
        # 3. Select Target Channel/Group
        try:
            tgt_choice = int(input(f"Select TARGET (to invite members to) (1-{len(chats)}): ").strip())
            if tgt_choice < 1 or tgt_choice > len(chats):
                print("Invalid target selection.")
                return
            if tgt_choice == src_choice:
                print("❌ Source and Target cannot be the same!")
                return
        except ValueError:
            print("Invalid input.")
            return

        target_chat = chats[tgt_choice - 1]
        target_chat_id = target_chat.id
        
        print(f"\nScraping members from source: '{source_chat.name}'...")
        scraped_users = []
        async for user in primary_client.iter_participants(source_chat.entity):
            # Skip bots and self
            if user.bot or user.is_self:
                continue
            scraped_users.append(user)

        print(f"✅ Successfully scraped {len(scraped_users)} members!")
        
        if not scraped_users:
            print("No members found to invite. Exiting.")
            return

        # 4. Input Delay
        try:
            delay_raw = input("\nEnter delay between invites in seconds (default: 30): ").strip()
            delay = float(delay_raw) if delay_raw else 30.0
            if delay < 15.0:
                print('⚠️ WARNING: Delay under 15s is extremely risky. Enforcing minimum safe delay of 15.0s')
                delay = 15.0
        except ValueError:
            print("⚠️ Invalid delay. Using default of 30 seconds.")
            delay = 30.0

    except Exception as e:
        print(f"❌ Error during chat resolution/scraping: {e}")
        return
    finally:
        await primary_client.disconnect()

    # 5. Distribute Members Randomly
    random.shuffle(scraped_users)
    
    account_assignments = {session: [] for session in selected_sessions}
    for idx, user in enumerate(scraped_users):
        assigned_session = selected_sessions[idx % len(selected_sessions)]
        account_assignments[assigned_session].append(user)

    # Preview distribution
    print("\n--- Invitation Plan ---")
    print(f"Source: {source_chat.name}")
    print(f"Target: {target_chat.name}")
    for session, targets in account_assignments.items():
        print(f"• Account {session}: assigned {len(targets)} members to invite.")

    confirm = input("\nDo you want to start the invitation process? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    print("\nStarting invitation process...")
    print("=" * 60)

    # Run invitations sequentially per account
    for session in selected_sessions:
        targets = account_assignments[session]
        if not targets:
            continue
            
        session_path = os.path.join(ACCOUNTS_DIR, session)
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
                print(f"❌ [{session}] Session is expired or unauthorized! Skipping.")
                continue

            me = await client.get_me()
            print(f"\n🔄 [{session}] Connecting as: {me.first_name} (+{me.phone or 'None'})")
            
            # Resolve target chat/channel on this account
            target_chat_entity = None
            dialogs = await client.get_dialogs()
            for d in dialogs:
                if (d.is_group or d.is_channel) and d.id == target_chat_id:
                    target_chat_entity = d.entity
                    break
            
            if not target_chat_entity:
                print(f"❌ [{session}] This account has not joined/subscribed to target '{target_chat.name}'! Skipping.")
                continue

            # Process targets assigned to this account
            for i, target_user in enumerate(targets):
                res = await add_single_user(client, target_chat_entity, target_user, session)
                
                if res == "RESTRICTED":
                    print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                    break
                
                # If hit a flood limit, wait and retry
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    if res > 60:
                        print(f"   ⚠️ Rate limit is too long ({res}s)! Skipping this account to save time.")
                        break
                    print(f"   🕒 Waiting {res}s due to rate limit...")
                    await asyncio.sleep(res)
                    # Retry once
                    res_retry = await add_single_user(client, target_chat_entity, target_user, session)
                    if res_retry == "RESTRICTED":
                        print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                        break
                
                # Apply custom delay between invites
                if i < len(targets) - 1:
                    print(f"   🕒 Waiting {delay}s delay...")
                    await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))

        except Exception as e:
            print(f"❌ [{session}] Error during process: {e}")
        finally:
            await client.disconnect()

    print("=" * 60)
    print("Channel/Group Invitation completed!")

if __name__ == "__main__":
    asyncio.run(main())
