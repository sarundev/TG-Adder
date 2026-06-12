import os
import re
import csv
import json
import csv
import random
import asyncio
import threading
from datetime import datetime, timezone
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient, events, functions
from telethon.tl.types import Channel, Chat, User, InputUser
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest, ImportChatInviteRequest
from telethon.errors import (
    FloodWaitError, 
    UserPrivacyRestrictedError, 
    UserAlreadyParticipantError,
    UserIdInvalidError,
    PeerFloodError,
    SessionPasswordNeededError,
    ChatWriteForbiddenError,
    ChatAdminRequiredError
)

app = FastAPI(title="Telegram Suite API")

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"
ACCOUNTS_DIR = "accounts"

# Global states
PENDING_CLIENTS = {}
LOG_BUFFER = []
SCRAPED_MEMBERS_CACHE = {}
ACTIVE_LISTENERS = {}
IS_INVITING = False

def log_msg(msg: str):
    LOG_BUFFER.append(msg)
    if len(LOG_BUFFER) > 1000:
        LOG_BUFFER.pop(0)

def get_saved_sessions():
    if not os.path.exists(ACCOUNTS_DIR):
        return []
    sessions = []
    for f in os.listdir(ACCOUNTS_DIR):
        if f.endswith(".session"):
            sessions.append(f[:-8])
    return sorted(sessions)

def parse_identifier(url: str):
    url = url.strip()
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if match:
        return match.group(1)
    if url.startswith('@'):
        return url[1:]
    return url

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    phone: str

class LoginConfirm(BaseModel):
    phone: str
    code: str
    password: Optional[str] = None

class ScrapeRequest(BaseModel):
    account: str
    group_url: str
    keyword: Optional[str] = None

class AccountRequest(BaseModel):
    account: str

class InviteRequest(BaseModel):
    accounts: List[str]
    target_group: str
    members: List[str]
    delay: float

class GroupToGroupInviteRequest(BaseModel):
    accounts: List[str]
    primary_account: str
    source_group: str
    target_group: str
    delay: float

class ApproverRequest(BaseModel):
    account: str
    group_url: str

class ApplyBoostRequest(BaseModel):
    account: str
    target_group: str
    slots: List[int]

class AutoBoostRequest(BaseModel):
    accounts: List[str]
    target_group: str
    max_boosts: Optional[int] = None

# --- License Models ---
class LicenseVerifyRequest(BaseModel):
    token: str
    hwid: str

class LicenseGenerateRequest(BaseModel):
    admin_key: str
    prefix: str = "TLG"

# --- Endpoints ---

import json
LICENSE_FILE = os.path.join(ACCOUNTS_DIR, "licenses.json")

def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    try:
        with open(LICENSE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_licenses(data):
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.post("/api/license/verify")
def verify_license(req: LicenseVerifyRequest):
    licenses = load_licenses()
    token = req.token.strip()
    hwid = req.hwid.strip()
    
    if token not in licenses:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    license_data = licenses[token]
    
    # If not claimed yet, bind to this HWID
    if not license_data.get("hwid"):
        license_data["hwid"] = hwid
        save_licenses(licenses)
        return {"status": "success", "detail": "Token bound to device successfully"}
        
    # If already claimed, verify HWID
    if license_data["hwid"] != hwid:
        raise HTTPException(status_code=401, detail="Token is already bound to another device")
        
    return {"status": "success", "detail": "Token verified"}

@app.post("/api/license/generate")
def generate_license(req: LicenseGenerateRequest):
    # Change 'admin123' to whatever secure password you want for generation
    if req.admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    import uuid
    new_token = f"{req.prefix}-{str(uuid.uuid4()).upper()[:8]}-{str(uuid.uuid4()).upper()[:8]}"
    
    licenses = load_licenses()
    licenses[new_token] = {"hwid": None, "created_at": datetime.now(timezone.utc).isoformat()}
    save_licenses(licenses)
    
    return {"status": "success", "token": new_token}


@app.get("/api/accounts")
def list_accounts():
    return {"accounts": get_saved_sessions()}

@app.post("/api/accounts/delete/{session_name}")
def delete_account(session_name: str):
    session_path = os.path.join(ACCOUNTS_DIR, f"{session_name}.session")
    if os.path.exists(session_path):
        os.remove(session_path)
    journal_path = session_path + "-journal"
    if os.path.exists(journal_path):
        os.remove(journal_path)
    return {"status": "ok"}

@app.post("/api/accounts/login/request")
async def login_request(req: LoginRequest):
    phone = req.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
        
    session_filename = phone.replace("+", "").replace(" ", "_")
    session_path = os.path.join(ACCOUNTS_DIR, session_filename)
    
    client = TelegramClient(session_path, API_ID, API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )
    await client.connect()
    
    try:
        if await client.is_user_authorized():
            await client.disconnect()
            return {"status": "authorized", "detail": "Already logged in"}
            
        await client.send_code_request(phone)
        PENDING_CLIENTS[phone] = client
        return {"status": "code_sent", "phone": phone}
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/login/confirm")
async def login_confirm(req: LoginConfirm):
    phone = req.phone
    code = req.code.strip()
    password = req.password.strip() if req.password else None
    
    if phone not in PENDING_CLIENTS:
        raise HTTPException(status_code=400, detail="No pending login request for this phone number")
        
    client = PENDING_CLIENTS[phone]
    
    try:
        if not password:
            try:
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                return {"status": "password_required", "phone": phone}
        else:
            await client.sign_in(password=password)
            
        user = await client.get_me()
        name = f"{user.first_name} {user.last_name or ''}".strip()
        
        # Cleanup pending mapping
        PENDING_CLIENTS.pop(phone)
        await client.disconnect()
        
        return {"status": "success", "user": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/details/{session_name}")
async def get_account_details(session_name: str):
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
            return {"status": "unauthorized"}
            
        user = await client.get_me()
        dialogs = await client.get_dialogs()
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        
        group_list = [{"id": g.id, "name": g.name} for g in groups]
        channels_count = sum(1 for d in dialogs if d.is_channel)
        pms_count = sum(1 for d in dialogs if d.is_user)
        
        return {
            "status": "authorized",
            "user_id": user.id,
            "name": f"{user.first_name} {user.last_name or ''}".strip(),
            "username": f"@{user.username}" if user.username else "None",
            "phone": f"+{user.phone}",
            "premium": user.premium,
            "groups_count": len(groups),
            "channels_count": channels_count,
            "pms_count": pms_count,
            "groups": group_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.disconnect()

@app.post("/api/scraper/scrape")
async def scrape_group(req: ScrapeRequest):
    session_name = req.account
    url = req.group_url.strip()
    keyword = req.keyword.strip() if req.keyword else None
    
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
            raise HTTPException(status_code=401, detail="Session expired or unauthorized")
            
        # Parse link type
        is_private = 'joinchat/' in url or '+' in url
        identifier = parse_identifier(url)
        
        group_entity = None
        if is_private:
            dialogs = await client.get_dialogs()
            if not keyword:
                raise HTTPException(status_code=400, detail="Keyword is required to search private group in chats")
            keyword_lower = keyword.lower()
            matches = [d for d in dialogs if d.is_group and keyword_lower in d.name.lower()]
            if not matches:
                raise HTTPException(status_code=404, detail="No matching joined group found")
            group_entity = matches[0].entity
            identifier = "".join([c if c.isalnum() else "_" for c in matches[0].name])
        else:
            group_entity = await client.get_entity(identifier)
            
        if not group_entity:
            raise HTTPException(status_code=404, detail="Could not resolve group entity")
            
        members = []
        async for user in client.iter_participants(group_entity):
            if user.bot or user.is_self or user.deleted:
                continue
            members.append({
                'id': user.id,
                'username': user.username or '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'phone': user.phone or '',
                'is_bot': 'Yes' if user.bot else 'No'
            })
            
        # Cache results for export
        cache_id = f"members_{identifier}"
        SCRAPED_MEMBERS_CACHE[cache_id] = members
        
        return {
            "status": "success",
            "count": len(members),
            "cache_id": cache_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.disconnect()

@app.get("/api/scraper/export/{cache_id}")
async def export_scraped_csv(cache_id: str):
    if cache_id not in SCRAPED_MEMBERS_CACHE:
        raise HTTPException(status_code=404, detail="Cache not found or expired")
    
    members = SCRAPED_MEMBERS_CACHE[cache_id]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "username", "first_name", "last_name", "phone", "is_bot"])
    writer.writeheader()
    for member in members:
        writer.writerow(member)
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={cache_id}.csv"}
    )

@app.post("/api/scraper/groups")
async def scrape_my_groups(req: AccountRequest):
    session_name = req.account
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
            raise HTTPException(status_code=401, detail="Session expired or unauthorized")
            
        dialogs = await client.get_dialogs()
        groups = []
        for d in dialogs:
            if d.is_group or d.is_channel:
                username = getattr(d.entity, 'username', None)
                link = f"https://t.me/{username}" if username else "Private/No Link"
                groups.append({
                    'id': d.id,
                    'name': d.name or 'Unknown',
                    'participants_count': getattr(d.entity, 'participants_count', 'Unknown'),
                    'link': link
                })
                
        cache_id = f"groups_{session_name}"
        SCRAPED_MEMBERS_CACHE[cache_id] = groups
        
        return {
            "status": "success",
            "count": len(groups),
            "cache_id": cache_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.disconnect()

@app.get("/api/scraper/export-groups/{cache_id}")
async def export_groups_csv(cache_id: str):
    if cache_id not in SCRAPED_MEMBERS_CACHE:
        raise HTTPException(status_code=404, detail="Cache not found or expired")
    
    groups = SCRAPED_MEMBERS_CACHE[cache_id]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "name", "participants_count", "link"])
    writer.writeheader()
    for group in groups:
        writer.writerow(group)
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={cache_id}.csv"}
    )

@app.get("/api/logs")
def get_logs():
    return {"logs": LOG_BUFFER}

@app.post("/api/logs/clear")
def clear_logs():
    LOG_BUFFER.clear()
    return {"status": "ok"}

# --- Inviter Background Thread Execution ---
async def add_single_user(client, target_entity, user_or_id, session_name):
    user_label = "Unknown User"
    try:
        if isinstance(user_or_id, User):
            user_entity = user_or_id
            user_label = f"@{user_entity.username}" if getattr(user_entity, 'username', None) else f"ID {getattr(user_entity, 'id', 'Unknown')}"
        else:
            user_entity = await client.get_entity(user_or_id)
            user_label = f"@{user_entity.username}" if getattr(user_entity, 'username', None) else f"ID {getattr(user_entity, 'id', 'Unknown')}"
        
        if isinstance(target_entity, Channel):
            await client(InviteToChannelRequest(target_entity, [user_entity]))
        elif isinstance(target_entity, Chat):
            await client(AddChatUserRequest(chat_id=target_entity.id, user_id=user_entity, fwd_limit=0))
        else:
            raise ValueError("Unsupported target entity")
            
        log_msg(f"   ✅ [{session_name}] Successfully added: {user_label}")
        return True
    except UserPrivacyRestrictedError:
        log_msg(f"   ⚠️ [{session_name}] Privacy settings restricted adding: {user_id_or_username}")
    except UserAlreadyParticipantError:
        log_msg(f"   ℹ️ [{session_name}] Already in channel/group: {user_id_or_username}")
    except UserIdInvalidError:
        log_msg(f"   ❌ [{session_name}] Invalid user identifier: {user_id_or_username}")
    except PeerFloodError:
        log_msg(f"   ❌ [{session_name}] Account has been flagged/restricted by Telegram (PeerFloodError)!")
        return "RESTRICTED"
    except (ChatWriteForbiddenError, ChatAdminRequiredError) as e:
        log_msg(f"   ❌ [{session_name}] Permission denied to add to chat. Attempting to bypass by ignoring...")
        return False
    except FloodWaitError as e:
        log_msg(f"   ⚠️ [{session_name}] Rate limited! Must wait {e.seconds}s.")
        return e.seconds
    except Exception as e:
        # Simplify the printed user label so the logs aren't massive
        short_label = user_label if isinstance(user_label, str) else "User"
        log_msg(f"   ❌ [{session_name}] Failed to add {short_label}: {type(e).__name__} - {e}")
    return False

async def invite_task_worker(accounts: List[str], target_group: str, members: List[str], delay: float):
    log_msg(f"\n==========================================")
    log_msg(f"🚀 INVITATION WEB TASK STARTED")
    log_msg(f"Targets: {len(members)} users | Accounts: {len(accounts)} | Delay: {delay}s")
    log_msg(f"==========================================")
    
    target_id = parse_identifier(target_group)
    
    # Shuffle and distribute targets
    random.shuffle(members)
    assignments = {acc: [] for acc in accounts}
    for idx, user in enumerate(members):
        acc = accounts[idx % len(accounts)]
        assignments[acc].append(user)
        
    for session in accounts:
        targets = assignments[session]
        if not targets:
            continue
            
        log_msg(f"\n🔄 [{session}] Connecting to invite {len(targets)} users...")
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
                log_msg(f"❌ [{session}] Unauthorized/Expired session. Skipping.")
                continue
                
            target_entity = None
            dialogs = await client.get_dialogs()
            for d in dialogs:
                if (d.is_group or d.is_channel) and (str(d.id) == target_id or d.name == target_id or getattr(d.entity, 'username', '') == target_id):
                    target_entity = d.entity
                    break
                    
            if not target_entity:
                try:
                    target_entity = await client.get_entity(target_id)
                except Exception:
                    log_msg(f"❌ [{session}] Could not resolve target: '{target_id}'. Skipping.")
                    continue

            for i, user in enumerate(targets):
                res = await add_single_user(client, target_entity, user, session)
                
                if res == "RESTRICTED":
                    log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                    break
                    
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    log_msg(f"   🕒 Waiting {res}s due to rate limit...")
                    await asyncio.sleep(res)
                    res_retry = await add_single_user(client, target_entity, user, session)
                    if res_retry == "RESTRICTED":
                        log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                        break
                        
                if i < len(targets) - 1:
                    await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))
                    
        except Exception as e:
            log_msg(f"❌ [{session}] Loop error: {e}")
        finally:
            await client.disconnect()
            
    log_msg(f"\n==========================================")
    log_msg(f"🎉 INVITATION WEB TASK COMPLETED")
    log_msg(f"==========================================")

async def group_to_group_invite_worker(accounts: List[str], primary_account: str, source_group: str, target_group: str, delay: float):
    log_msg(f"\n==========================================")
    log_msg(f"🚀 GROUP-TO-GROUP BROADCAST STARTED")
    log_msg(f"Primary Account: {primary_account} | Source Group: {source_group} | Target Group: {target_group}")
    log_msg(f"==========================================")
    
    primary_path = os.path.join(ACCOUNTS_DIR, primary_account)
    primary_client = TelegramClient(primary_path, API_ID, API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )
    scraped_users = []
    
    try:
        await primary_client.connect()
        if not await primary_client.is_user_authorized():
            log_msg(f"❌ Primary account '{primary_account}' is unauthorized. Scraping cancelled.")
            return
            
        source_id = parse_identifier(source_group)
        source_entity = None
        dialogs = await primary_client.get_dialogs()
        
        is_private = 'joinchat/' in source_group or '+' in source_group
        
        if is_private:
            for d in dialogs:
                if d.is_group and (source_id.lower() in d.name.lower() or source_id == str(d.id)):
                    source_entity = d.entity
                    break
        else:
            for d in dialogs:
                if (d.is_group or d.is_channel) and (str(d.id) == source_id or d.name == source_id or getattr(d.entity, 'username', '') == source_id):
                    source_entity = d.entity
                    break
            if not source_entity:
                try:
                    source_entity = await primary_client.get_entity(source_id)
                except Exception:
                    pass
                    
        if not source_entity:
            log_msg(f"❌ Could not resolve source group '{source_group}' on primary account.")
            return
            
        log_msg(f"Scraping members from: {getattr(source_entity, 'title', source_group)}...")
        async for user in primary_client.iter_participants(source_entity):
            if user.bot or user.is_self or user.deleted:
                continue
            scraped_users.append(user)
            
        log_msg(f"✅ Successfully scraped {len(scraped_users)} members.")
    except Exception as e:
        log_msg(f"❌ Scraping error: {e}")
        return
    finally:
        await primary_client.disconnect()
        
    if not scraped_users:
        log_msg("No members found. Invitation process stopped.")
        return
        
    random.shuffle(scraped_users)
    assignments = {acc: [] for acc in accounts}
    for idx, user in enumerate(scraped_users):
        acc = accounts[idx % len(accounts)]
        assignments[acc].append(user)
        
    target_id = parse_identifier(target_group)
    
    for session in accounts:
        targets = assignments[session]
        if not targets:
            continue
            
        log_msg(f"\n🔄 [{session}] Connecting to invite {len(targets)} users...")
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
                log_msg(f"❌ [{session}] Session is unauthorized/expired. Skipping.")
                continue
                
            target_entity = None
            dialogs = await client.get_dialogs()
            
            # ATTEMPT TO JOIN TARGET GROUP FIRST TO BYPASS WRITE FORBIDDEN
            is_private_target = 'joinchat/' in target_group or '+' in target_group
            try:
                if is_private_target:
                    match = re.search(r'(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', target_group)
                    if match:
                        await client(ImportChatInviteRequest(match.group(1)))
                else:
                    await client(JoinChannelRequest(target_id))
            except Exception:
                pass # Ignore if already joined or fails
                
            for d in dialogs:
                if (d.is_group or d.is_channel) and (str(d.id) == target_id or d.name == target_id or getattr(d.entity, 'username', '') == target_id):
                    target_entity = d.entity
                    break
            if not target_entity:
                try:
                    target_entity = await client.get_entity(target_id)
                except Exception:
                    log_msg(f"❌ [{session}] Could not resolve target: '{target_id}'. Skipping.")
                    continue

            for i, user_entity in enumerate(targets):
                res = await add_single_user(client, target_entity, user_entity, session)
                
                if res == "RESTRICTED":
                    log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                    break
                    
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    log_msg(f"   🕒 Waiting {res}s due to rate limit...")
                    await asyncio.sleep(res)
                    res_retry = await add_single_user(client, target_entity, user_entity, session)
                    if res_retry == "RESTRICTED":
                        log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                        break
                        
                if i < len(targets) - 1:
                    await asyncio.sleep(delay * __import__('random').uniform(0.8, 1.5))
                    
        except Exception as e:
            log_msg(f"❌ [{session}] Loop error: {e}")
        finally:
            await client.disconnect()
            
        log_msg(f"\n==========================================")
        log_msg(f"🎉 GROUP-TO-GROUP BROADCAST COMPLETED")
        log_msg(f"==========================================")

async def run_worker_safe(worker_func, *args):
    global IS_INVITING
    IS_INVITING = True
    try:
        await worker_func(*args)
    finally:
        IS_INVITING = False

@app.post("/api/inviter/invite-group")
async def start_group_to_group_inviter(req: GroupToGroupInviteRequest, background_tasks: BackgroundTasks):
    if IS_INVITING:
        raise HTTPException(status_code=400, detail="An inviter task is already running in the background. Please wait for it to finish or restart the server.")
    if not req.accounts:
        raise HTTPException(status_code=400, detail="No accounts specified")
    if not req.source_group or not req.target_group:
        raise HTTPException(status_code=400, detail="Source or target group missing")
        
    background_tasks.add_task(run_worker_safe, group_to_group_invite_worker, req.accounts, req.primary_account, req.source_group, req.target_group, req.delay)
    return {"status": "started"}

@app.post("/api/inviter/invite")
async def start_inviter(req: InviteRequest, background_tasks: BackgroundTasks):
    if IS_INVITING:
        raise HTTPException(status_code=400, detail="An inviter task is already running in the background. Please wait for it to finish or restart the server.")
    if not req.accounts:
        raise HTTPException(status_code=400, detail="No accounts specified")
    if not req.members:
        raise HTTPException(status_code=400, detail="No members to invite")
        
    background_tasks.add_task(
        run_worker_safe,
        invite_task_worker,
        req.accounts,
        req.target_group,
        req.members,
        req.delay
    )
    return {"status": "started", "targets": len(req.members), "accounts_used": len(req.accounts)}

@app.post("/api/inviter/invite-csv")
async def start_inviter_csv(
    background_tasks: BackgroundTasks,
    target_group: str = Form(...),
    accounts: str = Form(...),
    delay: float = Form(5.0),
    file: UploadFile = File(...)
):
    if IS_INVITING:
        raise HTTPException(status_code=400, detail="An inviter task is already running in the background. Please wait for it to finish or restart the server.")
    account_list = json.loads(accounts)
    
    if not account_list:
        raise HTTPException(status_code=400, detail="No accounts specified")
        
    contents = await file.read()
    csv_string = contents.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_string))
    
    members = []
    for row in csv_reader:
        if row.get("username"):
            members.append(row["username"])
        elif row.get("id"):
            members.append(int(row["id"]))
            
    if not members:
        raise HTTPException(status_code=400, detail="No valid users found in CSV")
        
    background_tasks.add_task(
        run_worker_safe,
        invite_task_worker,
        account_list,
        target_group,
        members,
        delay
    )
    return {"status": "started", "targets": len(members), "accounts_used": len(account_list)}

@app.on_event("shutdown")
async def shutdown_event():
    # Disconnect all active listeners on shutdown
    for session_name, client in list(ACTIVE_LISTENERS.items()):
        try:
            await client.disconnect()
        except Exception:
            pass
    ACTIVE_LISTENERS.clear()

@app.get("/api/approver/status")
def get_approver_status():
    return {"active_listeners": list(ACTIVE_LISTENERS.keys())}

@app.post("/api/approver/start")
async def start_approver(req: ApproverRequest):
    session_name = req.account
    group_url = req.group_url.strip()
    
    if session_name in ACTIVE_LISTENERS:
        try:
            old_client = ACTIVE_LISTENERS[session_name]
            await old_client.disconnect()
        except Exception:
            pass
        ACTIVE_LISTENERS.pop(session_name, None)
        
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
            await client.disconnect()
            raise HTTPException(status_code=401, detail="Session expired or unauthorized")
            
        group_id = parse_identifier(group_url)
        group_entity = await client.get_entity(group_id)
        group_title = getattr(group_entity, 'title', group_url)
        
        async def handler(event):
            try:
                await event.approve()
                log_msg(f"✅ [{session_name}] Approved join request from User ID {event.user_id} in group '{group_title}'")
            except Exception as e:
                log_msg(f"❌ [{session_name}] Failed to approve join request: {e}")
                
        client.add_event_handler(handler, events.JoinRequest(group_entity))
        ACTIVE_LISTENERS[session_name] = client
        log_msg(f"✉️ [{session_name}] Started auto-approve listener for '{group_title}'...")
        return {"status": "started", "group": group_title}
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approver/stop/{session_name}")
async def stop_approver(session_name: str):
    if session_name in ACTIVE_LISTENERS:
        try:
            client = ACTIVE_LISTENERS[session_name]
            await client.disconnect()
            log_msg(f"✉️ [{session_name}] Stopped auto-approve listener.")
        except Exception as e:
            log_msg(f"❌ [{session_name}] Error stopping listener: {e}")
        finally:
            ACTIVE_LISTENERS.pop(session_name, None)
        return {"status": "stopped"}
    return {"status": "not_running"}

@app.get("/api/boost/status/{session_name}")
async def get_boost_status(session_name: str):
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
            raise HTTPException(status_code=401, detail="Session expired or unauthorized")
        
        result = await client(functions.premium.GetMyBoostsRequest())
        
        # Build chats lookup map
        chat_map = {}
        for c in getattr(result, 'chats', []):
            chat_map[c.id] = getattr(c, 'title', 'Unknown Chat')
            if getattr(c, 'username', None):
                chat_map[c.id] = f"{c.title} (@{c.username})"
                
        # Parse my_boosts
        boost_slots = []
        for b in getattr(result, 'my_boosts', []):
            peer_title = None
            peer_id = None
            if b.peer:
                peer_id = getattr(b.peer, 'channel_id', getattr(b.peer, 'chat_id', getattr(b.peer, 'user_id', None)))
                if peer_id and peer_id in chat_map:
                    peer_title = chat_map[peer_id]
                else:
                    peer_title = f"Peer ID {peer_id}" if peer_id else "Unknown Peer"
            
            boost_slots.append({
                "slot": b.slot,
                "boosting": peer_title,
                "peer_id": peer_id,
                "expires": b.expires.isoformat() if b.expires else None,
                "cooldown_until": b.cooldown_until_date.isoformat() if b.cooldown_until_date else None
            })
            
        return {
            "status": "success",
            "slots": boost_slots
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.disconnect()

@app.post("/api/boost/apply")
async def apply_boost(req: ApplyBoostRequest):
    session_name = req.account
    target_group = req.target_group.strip()
    slots = req.slots
    
    if not slots:
        raise HTTPException(status_code=400, detail="At least one slot must be selected")
        
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
            raise HTTPException(status_code=401, detail="Session expired or unauthorized")
            
        # Determine group link type
        is_private = 'joinchat/' in target_group or '+' in target_group
        target_id = parse_identifier(target_group)
        
        target_entity = None
        try:
            target_entity = await client.get_entity(target_id)
        except Exception:
            log_msg(f"ℹ️ [{session_name}] Group/channel not recognized. Attempting to join first...")
            try:
                if is_private:
                    match = re.search(r'(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', target_group)
                    if match:
                        invite_hash = match.group(1)
                        await client(functions.messages.ImportChatInviteRequest(invite_hash))
                        log_msg(f"✅ [{session_name}] Joined private target group.")
                else:
                    await client(functions.channels.JoinChannelRequest(target_id))
                    log_msg(f"✅ [{session_name}] Joined public target channel.")
                
                target_entity = await client.get_entity(target_id)
            except Exception as join_err:
                log_msg(f"❌ [{session_name}] Failed to join group: {join_err}")
                raise HTTPException(status_code=400, detail=f"Failed to join group/channel: {join_err}. Please join manually and retry.")
        
        if not target_entity:
            raise HTTPException(status_code=404, detail="Could not find or resolve target channel/group.")
            
        await client(functions.premium.ApplyBoostRequest(peer=target_entity, slots=slots))
        log_msg(f"🚀 [{session_name}] Successfully applied boosts from slots {slots} to target '{target_group}'")
        return {"status": "success", "detail": f"Boosts applied to {target_group}"}
    except Exception as e:
        log_msg(f"❌ [{session_name}] Failed to apply boosts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.disconnect()

@app.post("/api/boost/auto")
async def auto_boost_channels(req: AutoBoostRequest):
    accounts = req.accounts
    target_group = req.target_group.strip()
    max_boosts = req.max_boosts
    
    if not accounts:
        raise HTTPException(status_code=400, detail="Select at least one account")
        
    log_msg(f"\n==========================================")
    log_msg(f"🚀 AUTO-BOOSTER BOT STARTED")
    log_msg(f"Target: {target_group} | Accounts: {len(accounts)}")
    log_msg(f"==========================================")
    
    boosts_applied = 0
    
    for session in accounts:
        if max_boosts is not None and boosts_applied >= max_boosts:
            break
            
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
                log_msg(f"❌ [{session}] Unauthorized/Expired session. Skipping.")
                continue
                
            # Get my boosts
            result = await client(functions.premium.GetMyBoostsRequest())
            free_slots = []
            
            for b in getattr(result, 'my_boosts', []):
                is_boosting = b.peer is not None
                is_cooldown = b.cooldown_until_date is not None and b.cooldown_until_date > datetime.now(timezone.utc)
                
                if not is_boosting and not is_cooldown:
                    free_slots.append(b.slot)
                    
            if not free_slots:
                log_msg(f"ℹ️ [{session}] No free boost slots available.")
                continue
                
            slots_to_use = free_slots
            if max_boosts is not None:
                remaining_needed = max_boosts - boosts_applied
                if len(slots_to_use) > remaining_needed:
                    slots_to_use = slots_to_use[:remaining_needed]
                    
            is_private = 'joinchat/' in target_group or '+' in target_group
            target_id = parse_identifier(target_group)
            target_entity = None
            
            try:
                target_entity = await client.get_entity(target_id)
            except Exception:
                log_msg(f"ℹ️ [{session}] Attempting to join target group...")
                try:
                    if is_private:
                        match = re.search(r'(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', target_group)
                        if match:
                            invite_hash = match.group(1)
                            await client(functions.messages.ImportChatInviteRequest(invite_hash))
                    else:
                        await client(functions.channels.JoinChannelRequest(target_id))
                    target_entity = await client.get_entity(target_id)
                except Exception as join_err:
                    log_msg(f"❌ [{session}] Failed to join group: {join_err}")
                    continue
            
            if not target_entity:
                log_msg(f"❌ [{session}] Could not resolve target entity. Skipping.")
                continue
                
            await client(functions.premium.ApplyBoostRequest(peer=target_entity, slots=slots_to_use))
            log_msg(f"✅ [{session}] Applied {len(slots_to_use)} boosts from slots {slots_to_use}")
            boosts_applied += len(slots_to_use)
            
        except Exception as e:
            log_msg(f"❌ [{session}] Boost error: {e}")
        finally:
            await client.disconnect()
            
    log_msg(f"\n==========================================")
    log_msg(f"🎉 AUTO-BOOSTER BOT COMPLETED")
    log_msg(f"Applied {boosts_applied} boosts to {target_group}")
    log_msg(f"==========================================")
    
    return {"status": "success", "boosts_applied": boosts_applied}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
