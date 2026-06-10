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
    PeerFloodError,
    UserNotMutualContactError,
    UserBannedInChannelError
)

import sys

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")

def get_saved_sessions():
    """Returns a list of saved session names from accounts/ folder."""
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    
    sessions = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.endswith(".session"):
            sessions.append(f[:-8])
    return sorted(sessions)

async def add_single_user(client, group_entity, user_entity, session_name):
    """Invites a single resolved user entity to a target group entity."""
    user_label = f"@{user_entity.username}" if user_entity.username else f"ID {user_entity.id}"
    try:
        if isinstance(group_entity, Channel):
            await client(InviteToChannelRequest(group_entity, [user_entity]))
        elif isinstance(group_entity, Chat):
            await client(AddChatUserRequest(chat_id=group_entity.id, user_id=user_entity, fwd_limit=0))
        else:
            raise ValueError(f"Unsupported group entity type: {type(group_entity)}")
            
        print(f"   ✅ [{session_name}] Successfully added: {user_label}")
        return True
    except UserPrivacyRestrictedError:
        print(f"   ⚠️ [{session_name}] Privacy settings restricted adding: {user_label}")
    except UserAlreadyParticipantError:
        print(f"   ℹ️ [{session_name}] Already in group: {user_label}")
    except UserIdInvalidError:
        print(f"   ❌ [{session_name}] Invalid user identifier: {user_label}")
    except (PeerFloodError, UserBannedInChannelError) as e:
        print(f"   ❌ [{session_name}] Account has been restricted/banned from inviting by Telegram ({type(e).__name__})!")
        return "RESTRICTED"
    except UserNotMutualContactError:
        print(f"   ❌ [{session_name}] Target is a basic group and user is not a contact. Upgrade target to a Supergroup!")
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
    print("   TELEGRAM GROUP SCRAPER & AUTO-INVITER     ")
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

    # Use the first selected account to scrape the group list
    primary_session = selected_sessions[0]
    primary_path = os.path.join(ACCOUNTS_DIR, primary_session)
    
    print(f"\nConnecting with primary account '{primary_session}' to fetch joined groups...")
    # Add realistic device details to prevent bans
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
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        
        if not groups:
            print("❌ This Telegram account is not joined to any groups or channels!")
            return

        print("\n--- Available Joined Groups & Channels ---")
        for idx, g in enumerate(groups, 1):
            print(f"{idx:02d}. {g.name:<30} | ID: {g.id}")

        # 2. Select Source Group
        try:
            src_choice = int(input(f"\nSelect SOURCE Group (to scrape members from) (1-{len(groups)}): ").strip())
            if src_choice < 1 or src_choice > len(groups):
                print("Invalid source selection.")
                return
        except ValueError:
            print("Invalid input.")
            return
        
        source_group = groups[src_choice - 1]
        
        # 3. Select Target Group
        try:
            tgt_choice = int(input(f"Select TARGET Group (to invite members to) (1-{len(groups)}): ").strip())
            if tgt_choice < 1 or tgt_choice > len(groups):
                print("Invalid target selection.")
                return
            if tgt_choice == src_choice:
                print("❌ Source and Target groups cannot be the same!")
                return
        except ValueError:
            print("Invalid input.")
            return

        target_group = groups[tgt_choice - 1]
        
        if isinstance(target_group.entity, Chat):
            print(f"\n⚠️ TARGET GROUP '{target_group.name}' is a Basic Group.")
            print("Telegram only allows adding mutual contacts to Basic Groups.")
            print("Automatically upgrading it to a Supergroup to bypass this restriction...")
            ans = 'y'
            if ans == 'y':
                try:
                    from telethon.tl.functions.messages import MigrateChatRequest
                    print("Upgrading group...")
                    updates = await primary_client(MigrateChatRequest(chat_id=target_group.entity.id))
                    
                    # Refresh dialogs to find the new supergroup
                    dialogs = await primary_client.get_dialogs()
                    new_group = None
                    # The supergroup will have the same title, but it's a Channel now
                    for d in dialogs:
                        if d.name == target_group.name and isinstance(d.entity, Channel):
                            new_group = d
                            break
                    
                    if new_group:
                        target_group = new_group
                        print(f"✅ Upgraded successfully! New Supergroup ID: {target_group.id}")
                    else:
                        print("⚠️ Upgraded, but couldn't locate the new supergroup in dialogs. Might fail.")
                except Exception as e:
                    print(f"❌ Failed to upgrade group: {e}")
                    print("Continuing with basic group, but invites will likely fail.")
            else:
                print("Proceeding without upgrade. (Invites will likely fail due to contact restrictions)")

        # Get target group ID (needed for resolution by other accounts)
        target_group_id = target_group.id
        
        print(f"\nScraping members from source group '{source_group.name}'...")
        scraped_users = []
        
        print("1. Standard Scrape (Requires member list to be public)")
        print("2. History Scrape (Bypasses hidden members, gets active chatters)")
        scrape_method = input("Select scraping method (1 or 2): ").strip()
        
        if scrape_method == '2':
            try:
                msg_limit_raw = input("How many recent messages to scan? (default: 5000): ").strip()
                msg_limit = int(msg_limit_raw) if msg_limit_raw else 5000
            except ValueError:
                msg_limit = 5000
                
            print(f"Scanning the last {msg_limit} messages... this might take a minute.")
            seen_ids = set()
            async for message in primary_client.iter_messages(source_group.entity, limit=msg_limit):
                user = message.sender
                if user and hasattr(user, 'bot') and not user.bot and not user.is_self and user.id not in seen_ids:
                    seen_ids.add(user.id)
                    scraped_users.append(user)
        else:
            try:
                async for user in primary_client.iter_participants(source_group.entity):
                    # Skip bots and self
                    if user.bot or user.is_self:
                        continue
                    scraped_users.append(user)
            except Exception as e:
                print(f"❌ Failed to get member list: {e}")
                print("⚠️ The group admins hid the member list! Automatically falling back to 'History Scrape' (Scanning active chatters)...")
                try:
                    msg_limit_raw = input("How many recent messages to scan? (default: 5000): ").strip()
                    msg_limit = int(msg_limit_raw) if msg_limit_raw else 5000
                except ValueError:
                    msg_limit = 5000
                    
                print(f"Scanning the last {msg_limit} messages... this might take a minute.")
                seen_ids = set()
                async for message in primary_client.iter_messages(source_group.entity, limit=msg_limit):
                    user = message.sender
                    if user and hasattr(user, 'bot') and not user.bot and not user.is_self and user.id not in seen_ids:
                        seen_ids.add(user.id)
                        scraped_users.append(user)

        print(f"✅ Successfully scraped {len(scraped_users)} members!")
        
        if not scraped_users:
            print("No members to invite. Exiting.")
            return

        # 4. Input Delay and Max Adds
        try:
            delay_raw = input("\nEnter delay between invites in seconds (default: 30): ").strip()
            delay = float(delay_raw) if delay_raw else 30.0
            if delay < 15.0:
                print('⚠️ WARNING: Delay under 15s is extremely risky. Enforcing minimum safe delay of 15.0s')
                delay = 15.0
        except ValueError:
            print("⚠️ Invalid delay. Using default of 30 seconds.")
            delay = 30.0

        try:
            max_adds_raw = input("\nHow many members do you want to add in total? (Press Enter to add all): ").strip()
            max_adds = int(max_adds_raw) if max_adds_raw else len(scraped_users)
            if max_adds <= 0:
                max_adds = len(scraped_users)
        except ValueError:
            print("⚠️ Invalid number. Will add all scraped users.")
            max_adds = len(scraped_users)

    except Exception as e:
        print(f"❌ Error during group resolution/scraping: {e}")
        return
    finally:
        await primary_client.disconnect()

    # 5. Distribute Members Randomly among inviting accounts
    random.shuffle(scraped_users)
    # Apply the user limit
    scraped_users = scraped_users[:max_adds]
    
    account_assignments = {session: [] for session in selected_sessions}
    for idx, user in enumerate(scraped_users):
        assigned_session = selected_sessions[idx % len(selected_sessions)]
        account_assignments[assigned_session].append(user)

    # Preview distribution
    print("\n--- Invitation Plan ---")
    print(f"Source Group: {source_group.name}")
    print(f"Target Group: {target_group.name}")
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
        # Add realistic device details to prevent bans
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
        
        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"❌ [{session}] Session is expired or unauthorized! Skipping.")
                continue

            me = await client.get_me()
            print(f"\n🔄 [{session}] Connecting as: {me.first_name} (+{me.phone or 'None'})")
            
            # Resolve target group on this account
            # (Account must already be joined to this group)
            target_group_entity = None
            dialogs = await client.get_dialogs()
            for d in dialogs:
                if d.is_group and d.id == target_group_id:
                    target_group_entity = d.entity
                    break
            
            if not target_group_entity:
                print(f"❌ [{session}] This account has not joined the target group '{target_group.name}'! Skipping.")
                continue

            # Process targets assigned to this account
            for i, target_user in enumerate(targets):
                res = await add_single_user(client, target_group_entity, target_user, session)
                
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
                    res_retry = await add_single_user(client, target_group_entity, target_user, session)
                    if res_retry == "RESTRICTED":
                        print(f"   ⚠️ [{session}] Breaking invite loop for this account to prevent permanent ban.")
                        break
                
                # Apply custom randomized delay between successful/attempted invites to avoid bans
                if i < len(targets) - 1:
                    # Randomize delay between 0.8x and 1.5x of user's delay
                    actual_delay = delay * random.uniform(0.8, 1.5)
                    print(f"   🕒 Waiting {actual_delay:.1f}s (randomized from {delay}s) to mimic human behavior...")
                    await asyncio.sleep(actual_delay)

        except Exception as e:
            print(f"❌ [{session}] Error during process: {e}")
        finally:
            await client.disconnect()

    print("=" * 60)
    print("Group-to-Group Invitation completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Program interrupted by user.")
    finally:
        os._exit(0)
