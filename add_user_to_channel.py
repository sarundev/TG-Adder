import os
import re
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

def parse_channel_identifier(url):
    """Extracts the username or ID from a channel link or input."""
    url = url.strip()
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if match:
        return match.group(1)
    if url.startswith('@'):
        return url[1:]
    return url

async def add_single_user(client, target_entity, user_to_add, session_name):
    """Invites a single user to a channel or group entity using the client."""
    user_label = user_to_add
    try:
        # Resolve target user entity
        resolved_user = await client.get_entity(user_to_add)
        user_label = f"@{resolved_user.username}" if resolved_user.username else f"ID {resolved_user.id}"
        
        if isinstance(target_entity, Channel):
            # Invite user using Telethon helper or InviteToChannelRequest (Channels & Supergroups)
            await client(InviteToChannelRequest(target_entity, [resolved_user]))
        elif isinstance(target_entity, Chat):
            # Invite user using legacy group AddChatUserRequest
            await client(AddChatUserRequest(chat_id=target_entity.id, user_id=resolved_user, fwd_limit=0))
        else:
            raise ValueError(f"Unsupported group/channel entity type: {type(target_entity)}")
            
        print(f"   ✅ [{session_name}] Successfully added: {user_label}")
        return True
    except UserPrivacyRestrictedError:
        print(f"   ⚠️ [{session_name}] Privacy settings restricted adding: {user_label}")
    except UserAlreadyParticipantError:
        print(f"   ℹ️ [{session_name}] Already in channel/group: {user_label}")
    except UserIdInvalidError:
        print(f"   ❌ [{session_name}] Invalid username/ID: {user_label}")
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
    print("      TELEGRAM CHANNEL AUTO-ADDER (INVITER)  ")
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

    # 2. Select Target Channel
    primary_session = selected_sessions[0]
    primary_path = os.path.join(ACCOUNTS_DIR, primary_session)
    
    print(f"\nConnecting with primary account '{primary_session}' to fetch joined channels...")
    primary_client = TelegramClient(
        primary_path, 
        API_ID, 
        API_HASH,
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
        channels_and_groups = [d for d in dialogs if d.is_channel or d.is_group]
        
        if not channels_and_groups:
            print("❌ This Telegram account is not joined to any channels or groups!")
            return

        print("\n--- Available Joined Channels & Groups ---")
        for idx, c in enumerate(channels_and_groups, 1):
            print(f"{idx:02d}. {c.name:<30} | ID: {c.id}")

        try:
            tgt_choice = int(input(f"\nSelect TARGET Channel (to invite members to) (1-{len(channels_and_groups)}): ").strip())
            if tgt_choice < 1 or tgt_choice > len(channels_and_groups):
                print("Invalid target selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
            
        target_entity_wrapper = channels_and_groups[tgt_choice - 1]
        target_id = target_entity_wrapper.id
        
        if isinstance(target_entity_wrapper.entity, Chat):
            print(f"\n⚠️ TARGET '{target_entity_wrapper.name}' is a Basic Group.")
            print("Basic Groups have heavy restrictions. Invites might fail if you are not a mutual contact.")
            
    except Exception as e:
        print(f"❌ Error fetching channels: {e}")
        return
    finally:
        await primary_client.disconnect()

    # 3. Input Members to Add
    print("\nEnter members/text (you can paste multiple lines).")
    print("When you are done, just press ENTER twice (leave a blank line):")
    
    lines = []
    while True:
        try:
            line = input()
            if not line.strip() and not lines:
                continue # ignore leading blank lines
            elif not line.strip():
                break # blank line after content means finish
            lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            break
    
    raw_members = "".join(lines)
    member_list = [m.strip() for m in re.split(r'[\n,]+', raw_members) if m.strip()]
    
    # Deduplicate member list
    member_list = list(set(member_list))
    if not member_list:
        print("❌ No valid members to add! Exiting.")
        return
    print(f"Loaded {len(member_list)} unique target members.")

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

    # 5. Distribute Members Randomly
    random.shuffle(member_list)
    
    account_assignments = {session: [] for session in selected_sessions}
    for idx, member in enumerate(member_list):
        assigned_session = selected_sessions[idx % len(selected_sessions)]
        account_assignments[assigned_session].append(member)

    # Preview distribution
    print("\n--- Distribution Plan ---")
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
            
            # Resolve target group/channel
            try:
                target_entity = await client.get_entity(target_id)
            except Exception as e:
                print(f"❌ [{session}] Could not resolve target entity '{target_id}': {e}. Skipping.")
                continue

            # Process targets assigned to this account
            for i, target in enumerate(targets):
                res = await add_single_user(client, target_entity, target, session)
                
                if res == "RESTRICTED":
                    print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                    break
                
                # If hit a flood limit, wait and retry or adapt
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    if res > 60:
                        print(f"   ⚠️ Rate limit is too long ({res}s)! Skipping this account to save time.")
                        break
                    print(f"   🕒 Waiting {res}s due to rate limit...")
                    await asyncio.sleep(res)
                    # Retry once
                    res_retry = await add_single_user(client, target_entity, target, session)
                    if res_retry == "RESTRICTED":
                        print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                        break
                
                # Apply custom randomized delay between successful/attempted invites
                if i < len(targets) - 1:
                    actual_delay = delay * __import__('random').uniform(0.8, 1.5)
                    print(f"   🕒 Waiting {actual_delay:.1f}s (randomized from {delay}s)...")
                    await asyncio.sleep(actual_delay)

        except Exception as e:
            print(f"❌ [{session}] Error during process: {e}")
        finally:
            await client.disconnect()

    print("=" * 60)
    print("Invitation process completed!")

if __name__ == "__main__":
    asyncio.run(main())
