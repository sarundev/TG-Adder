import os
import re
import random
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
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

def parse_group_identifier(url):
    """Extracts the username or ID from a group link or input."""
    url = url.strip()
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if match:
        return match.group(1)
    if url.startswith('@'):
        return url[1:]
    return url

async def add_single_user(client, group_entity, user_to_add, session_name):
    """Invites a single user to a group entity using the client."""
    try:
        # Resolve target user entity
        resolved_user = await client.get_entity(user_to_add)
        
        from telethon.tl.types import Channel, Chat
        from telethon.tl.functions.channels import InviteToChannelRequest
        from telethon.tl.functions.messages import AddChatUserRequest
        
        if isinstance(group_entity, Channel):
            # Invite user using Telethon helper or InviteToChannelRequest
            await client(InviteToChannelRequest(group_entity, [resolved_user]))
        elif isinstance(group_entity, Chat):
            # Invite user using legacy group AddChatUserRequest
            await client(AddChatUserRequest(chat_id=group_entity.id, user_id=resolved_user, fwd_limit=0))
        else:
            raise ValueError(f"Unsupported group entity type: {type(group_entity)}")
            
        print(f"   ✅ [{session_name}] Successfully added: {user_to_add}")
        return True
    except UserPrivacyRestrictedError:
        print(f"   ⚠️ [{session_name}] Privacy settings restricted adding: {user_to_add}")
    except UserAlreadyParticipantError:
        print(f"   ℹ️ [{session_name}] Already in group: {user_to_add}")
    except UserIdInvalidError:
        print(f"   ❌ [{session_name}] Invalid username/ID: {user_to_add}")
    except PeerFloodError:
        print(f"   ❌ [{session_name}] Account has been flagged/restricted by Telegram (PeerFloodError)!")
        return "RESTRICTED"
    except FloodWaitError as e:
        print(f"   ⚠️ [{session_name}] Rate limited! Must wait {e.seconds}s.")
        return e.seconds
    except Exception as e:
        print(f"   ❌ [{session_name}] Failed to add {user_to_add}: {e}")
    return False

async def main():
    sessions = get_saved_sessions()
    if not sessions:
        print("\nNo saved accounts found in accounts/ directory.")
        return

    print("\n======================================")
    print("      TELEGRAM AUTO-ADDER (INVITER)   ")
    print("======================================")
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

    # 2. Input Group Link
    group_url = input("\nEnter target group link or username (e.g., t.me/groupname): ").strip()
    if not group_url:
        print("❌ Group link cannot be empty!")
        return
    group_id = parse_group_identifier(group_url)

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
    
    raw_members = "\n".join(lines)
    # Split by comma or whitespace/newline and filter out empty strings
    member_list = [m.strip() for m in re.split(r'[\n,\s@]+', raw_members) if m.strip()]
    
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
    # Shuffle list
    random.shuffle(member_list)
    
    # Assign target slices to each account
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

    # Run the invitations sequentially per account
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
            
            # Resolve target group
            try:
                group_entity = await client.get_entity(group_id)
            except Exception as e:
                print(f"❌ [{session}] Could not resolve group entity '{group_id}': {e}. Skipping.")
                continue

            # Process targets assigned to this account
            for i, target in enumerate(targets):
                res = await add_single_user(client, group_entity, target, session)
                
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
                    res_retry = await add_single_user(client, group_entity, target, session)
                    if res_retry == "RESTRICTED":
                        print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                        break
                
                # Apply custom delay between successful/attempted invites
                if i < len(targets) - 1:
                    print(f"   🕒 Waiting {delay}s delay...")
                    await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))

        except Exception as e:
            print(f"❌ [{session}] Error during process: {e}")
        finally:
            await client.disconnect()

    print("=" * 60)
    print("Invitation process completed!")

if __name__ == "__main__":
    asyncio.run(main())
