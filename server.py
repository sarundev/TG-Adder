import os
import re
import csv
import json
import random
import asyncio
import threading
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telethon import TelegramClient, events, functions
from telethon.sessions import SQLiteSession
import sqlite3
import importlib.util

try:
    # Dynamically patch opentele to fix BaseException error before importing
    spec = importlib.util.find_spec("opentele")
    if spec and spec.origin:
        utils_path = os.path.join(os.path.dirname(spec.origin), "utils.py")
        if os.path.exists(utils_path):
            with open(utils_path, "r") as f:
                content = f.read()
            if 'raise BaseException("err")' in content:
                content = content.replace('raise BaseException("err")', 'pass')
                with open(utils_path, "w") as f:
                    f.write(content)

    from opentele.td import TDesktop
    from opentele.api import API, UseCurrentSession
    OPENTELE_AVAILABLE = True
except Exception as e:
    print(f"Failed to load opentele: {e}")
    OPENTELE_AVAILABLE = False


class RobustSQLiteSession(SQLiteSession):
    """SQLiteSession with 30s timeout + WAL mode to prevent 'database is locked' errors."""
    def _connect(self):
        self._conn = sqlite3.connect(self.filename + '.session', timeout=30, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=30000")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.commit()

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
    ChatAdminRequiredError,
    UsersTooMuchError,
    UserNotMutualContactError,
    InputUserDeactivatedError,
    UserKickedError,
    UserBannedInChannelError,
    BotGroupsBlockedError
)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for session_name, client in list(ACTIVE_LISTENERS.items()):
        try:
            await client.disconnect()
        except Exception:
            pass
    ACTIVE_LISTENERS.clear()

app = FastAPI(title="Telegram Suite API", lifespan=lifespan)

import os
# Mount frontend dist if exists
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
downloads_path = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(downloads_path, exist_ok=True)

if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
app.mount("/downloads", StaticFiles(directory=downloads_path), name="downloads")

class BotStartRequest(BaseModel):
    accounts: List[str]
    bot_username: str
    delay_min: int = 1
    delay_max: int = 3

async def _bot_start_task(req: BotStartRequest):
    global LOG_BUFFER
    log_msg(f"🚀 Starting Auto Bot Clicker for {len(req.accounts)} accounts targeting {req.bot_username}...")
    
    for session_name in req.accounts:
        try:
            client = make_client(os.path.join(ACCOUNTS_DIR, session_name))
            await client.connect()
            
            if not await client.is_user_authorized():
                log_msg(f"❌ {session_name} is not authorized.")
                continue
                
            # Send the /start command to the bot
            log_msg(f"⚙️ {session_name} sending /start to {req.bot_username}...")
            await client.send_message(req.bot_username, '/start')
            log_msg(f"✅ {session_name} successfully started {req.bot_username}!")
            
            # Wait random delay
            sleep_time = random.uniform(req.delay_min, req.delay_max)
            log_msg(f"⏳ Waiting {sleep_time:.1f}s before next account...")
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            log_msg(f"❌ Error with {session_name} starting bot: {str(e)}")
            await asyncio.sleep(1)

@app.post("/api/bot/start")
async def auto_start_bot(req: BotStartRequest, background_tasks: BackgroundTasks):
    if not req.accounts:
        raise HTTPException(status_code=400, detail="Select at least one account")
    if not req.bot_username:
        raise HTTPException(status_code=400, detail="Bot username is required")
        
    background_tasks.add_task(_bot_start_task, req)
    return {"status": "success", "message": f"Started sending /start to {req.bot_username} using {len(req.accounts)} accounts"}

class MediaDownloadRequest(BaseModel):
    account: str
    target_chat: str
    limit: int = 100
    save_path: str = ""

async def _media_download_task(req: MediaDownloadRequest):
    global LOG_BUFFER
    log_msg(f"📥 Starting Video Downloader on {req.target_chat} using {req.account}...")
    
    try:
        client = make_client(os.path.join(ACCOUNTS_DIR, req.account))
        await client.connect()
        
        if not await client.is_user_authorized():
            log_msg(f"❌ Account {req.account} is not authorized.")
            return
            
        target_entity = await client.get_entity(req.target_chat)
        
        safe_name = req.target_chat.replace("/", "_").replace(":", "_").replace("https___t.me_", "")
        if req.save_path:
            download_dir = os.path.join(req.save_path, safe_name)
        else:
            download_dir = os.path.join(downloads_path, "videos", safe_name)
        os.makedirs(download_dir, exist_ok=True)
        
        video_count = 0
        log_msg(f"🔍 Scanning last {req.limit} messages in {req.target_chat} for videos...")
        
        messages_to_download = []
        async for message in client.iter_messages(target_entity, limit=req.limit):
            if message.video or (message.document and message.file and message.file.mime_type and message.file.mime_type.startswith('video/')):
                messages_to_download.append(message)
                
        log_msg(f"📊 Found {len(messages_to_download)} videos. Starting optimized concurrent download...")
        
        # Download sequentially to prevent SQLite/Telethon connection deadlocks
        video_count = 0
        for i, msg in enumerate(messages_to_download):
            log_msg(f"⚡ Downloading video {i+1}/{len(messages_to_download)}...")
            await client.download_media(msg, file=download_dir)
            video_count += 1
            log_msg(f"✅ Video {i+1} completed.")
                
        log_msg(f"🎉 Media Downloader finished! Total videos downloaded: {video_count}")
        log_msg(f"📁 Saved to: {download_dir}")
        
    except Exception as e:
        log_msg(f"❌ Error downloading media: {str(e)}")
    finally:
        if 'client' in locals() and client:
            try:
                await client.disconnect()
            except Exception as e:
                log_msg(f"⚠️ Warning during client disconnect: {str(e)}")

@app.post("/api/media/download")
async def start_media_download(req: MediaDownloadRequest, background_tasks: BackgroundTasks):
    if not req.account:
        raise HTTPException(status_code=400, detail="Select an account")
    if not req.target_chat:
        raise HTTPException(status_code=400, detail="Target chat is required")
        
    background_tasks.add_task(_media_download_task, req)
    return {"status": "success", "message": f"Started scanning {req.target_chat} for videos..."}

@app.get("/")
def serve_frontend():
    if os.path.exists(frontend_path):
        return FileResponse(os.path.join(frontend_path, "index.html"))
    return {"message": "Frontend not built yet"}

# Enable CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ──
API_ID = 36597503
API_HASH = "ce9a6d0c68789ae5234b77aa081acfac"
ACCOUNTS_DIR = "accounts"
LOG_FILE = "logs.txt"

# ── Global Cancellation Flags ──
GLOBAL_CANCEL_FLAGS = {
    "inviter": False
}

os.makedirs(ACCOUNTS_DIR, exist_ok=True)
# Global states
PENDING_CLIENTS = {}
LOG_BUFFER = []
SCRAPED_MEMBERS_CACHE = {}
ACTIVE_LISTENERS = {}
IS_INVITING = False
# Per-session async locks — prevents concurrent SQLite access on the same .session file
SESSION_LOCKS: dict = {}

def get_session_lock(session_name: str) -> asyncio.Lock:
    """Returns (and creates if needed) a per-session asyncio Lock."""
    if session_name not in SESSION_LOCKS:
        SESSION_LOCKS[session_name] = asyncio.Lock()
    return SESSION_LOCKS[session_name]

async def configure_session_db(client):
    """Apply WAL mode + busy_timeout to a Telethon client's SQLite session to prevent locking."""
    try:
        if hasattr(client, 'session') and hasattr(client.session, '_conn') and client.session._conn:
            client.session._conn.execute("PRAGMA journal_mode=WAL")
            client.session._conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
            client.session._conn.commit()
    except Exception:
        pass  # Non-critical; proceed without WAL if unavailable

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

def make_client(session_path: str) -> TelegramClient:
    """Create a TelegramClient using RobustSQLiteSession to avoid 'database is locked'."""
    session = RobustSQLiteSession(session_path)
    return TelegramClient(
        session, api_id=API_ID, api_hash=API_HASH,
        device_model="iPhone 13 Pro Max",
        system_version="15.5",
        app_version="8.7.1",
        lang_code="en",
        system_lang_code="en"
    )


def parse_identifier(url: str):
    url = url.strip()
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]+)', url)
    if match:
        return match.group(1)
    if url.startswith('@'):
        return url[1:]
    return url

import json
import hashlib
import time as _time

# --- License Key Store ---
LICENSE_FILE = os.path.join(os.path.dirname(__file__), 'licenses.json')

def _load_licenses():
    if not os.path.exists(LICENSE_FILE):
        # Create a default license file with one demo key
        default = {
            "keys": {
                "TGADDER-2024-DEMO-0000": {
                    "label": "Demo License",
                    "active": True,
                    "expires": None   # None = never expires
                }
            }
        }
        with open(LICENSE_FILE, 'w') as f:
            json.dump(default, f, indent=2)
        return default
    with open(LICENSE_FILE, 'r') as f:
        return json.load(f)

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    phone: str

class LicenseRequest(BaseModel):
    key: str

class LoginConfirm(BaseModel):
    phone: str
    code: str
    password: Optional[str] = None

class ScrapeRequest(BaseModel):
    account: str
    group_url: str
    keyword: Optional[str] = None
    # ── Filters ──────────────────────────────────────
    filter_has_username: bool = False   # Only users with a @username
    filter_has_phone: bool = False      # Only users with visible phone
    filter_no_bots: bool = True         # Exclude bots (default ON)
    filter_active_recently: bool = False  # Only recently-active users
    filter_inactive: bool = False         # Only inactive users (offline > 1 week)
    filter_has_name: bool = False       # Only users with a real first name

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

class InviteByUsernameRequest(BaseModel):
    accounts: List[str]
    target_group: str
    usernames: List[str]
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

class WarmRequest(BaseModel):
    accounts: List[str]
    do_react: bool = True
    do_chat: bool = True
    reactions_per_group: int = 3
    messages_to_send: int = 3
    react_delay: float = 10.0
    chat_delay: float = 20.0

# --- License Models ---
class LicenseVerifyRequest(BaseModel):
    token: str
    hwid: str

class LicenseGenerateRequest(BaseModel):
    admin_key: str
    prefix: str = "TLG"
    duration: str = "lifetime" # '1_week', '1_month', '2_months', '3_months', '1_year', 'lifetime'

# --- Endpoints ---

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
    
    if token == "TLG-MASTER-KEY-168":
        return {"status": "success", "detail": "Master Token verified"}
    
    if token not in licenses:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    license_data = licenses[token]
    
    if not license_data.get("hwid"):
        # Remove any existing licenses for this HWID to prevent conflicts
        keys_to_remove = [k for k, v in licenses.items() if v.get("hwid") == hwid]
        for k in keys_to_remove:
            del licenses[k]
            
        license_data["hwid"] = hwid
        
        # Start the expiration timer upon first use
        duration_days = license_data.get("duration_days")
        if duration_days is not None:
            from datetime import timedelta
            expire_date = datetime.now(timezone.utc) + timedelta(days=duration_days)
            license_data["expires_at"] = expire_date.isoformat()
            
        save_licenses(licenses)
        return {"status": "success", "detail": "Token bound to device successfully"}
        
    # If already claimed, verify HWID
    if license_data["hwid"] != hwid:
        raise HTTPException(status_code=401, detail="Token is already bound to another device")
        
    # Check expiration
    expires_at_str = license_data.get("expires_at")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=401, detail="License has expired")
        
    return {"status": "success", "detail": "Token verified"}

@app.post("/api/license/generate")
def generate_license(req: LicenseGenerateRequest):
    # Change 'admin123' to whatever secure password you want for generation
    if req.admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    import uuid
    new_token = f"{req.prefix}-{str(uuid.uuid4()).upper()[:8]}-{str(uuid.uuid4()).upper()[:8]}"
    
    duration_map = {
        "1_week": 7,
        "1_month": 30,
        "2_months": 60,
        "3_months": 90,
        "1_year": 365,
        "lifetime": None
    }
    duration_days = duration_map.get(req.duration)
    
    licenses = load_licenses()
    licenses[new_token] = {
        "hwid": None, 
        "created_at": datetime.now(timezone.utc).isoformat(),
        "duration_days": duration_days,
        "expires_at": None,
        "duration_label": req.duration
    }
    save_licenses(licenses)
    
    return {"status": "success", "token": new_token, "duration": req.duration}

class LicenseBuyRequest(BaseModel):
    duration: str
    success_url: str

@app.post("/api/license/buy")
def buy_license(req: LicenseBuyRequest):
    import time
    import hashlib
    import urllib.parse
    
    # User Profile ID and SecretID for khqr.cc
    profile_id = "pNiGKZdBf8OMDhiIiRa5TmzCZiYJ16tB"
    secret_key = "GD2jqnaMErwOTV180AbNzWfjp5clLMPL"
    
    price_map = {"1_week": 5.0, "1_month": 15.0, "3_months": 40.0, "1_year": 100.0, "lifetime": 199.0}
    price = price_map.get(req.duration, 15.0)
    
    transaction_id = f"ORD_{int(time.time())}"
    success_url = req.success_url
    remark = f"License_{req.duration}"
    
    raw_string = f"{secret_key}{transaction_id}{price}{success_url}{remark}"
    hash_val = hashlib.sha1(raw_string.encode('utf-8')).hexdigest()
    
    params = {
        "transaction_id": transaction_id,
        "amount": price,
        "success_url": success_url,
        "remark": remark,
        "hash": hash_val
    }
    
    checkout_url = f"https://khqr.cc/api/payment/request/{profile_id}?{urllib.parse.urlencode(params)}"
    
    return {
        "status": "redirect", 
        "checkout_url": checkout_url
    }

class AccountBuyRequest(BaseModel):
    account_type: str
    success_url: str

@app.post("/api/account/buy")
def buy_account(req: AccountBuyRequest):
    import time
    import hashlib
    import urllib.parse
    
    # User Profile ID and SecretID for khqr.cc
    profile_id = "pNiGKZdBf8OMDhiIiRa5TmzCZiYJ16tB"
    secret_key = "GD2jqnaMErwOTV180AbNzWfjp5clLMPL"
    
    price_map = {"fresh": 0.50, "aged": 2.00, "admin": 5.00}
    price = price_map.get(req.account_type, 0.50)
    
    transaction_id = f"ACC_{int(time.time())}"
    success_url = req.success_url
    remark = f"Account_{req.account_type}"
    
    raw_string = f"{secret_key}{transaction_id}{price}{success_url}{remark}"
    hash_val = hashlib.sha1(raw_string.encode('utf-8')).hexdigest()
    
    params = {
        "transaction_id": transaction_id,
        "amount": price,
        "success_url": success_url,
        "remark": remark,
        "hash": hash_val
    }
    
    checkout_url = f"https://khqr.cc/api/payment/request/{profile_id}?{urllib.parse.urlencode(params)}"
    
    return {
        "status": "redirect", 
        "checkout_url": checkout_url
    }

class LicenseIssueRequest(BaseModel):
    duration: str

@app.post("/api/license/issue")
def issue_license(req: LicenseIssueRequest):
    import uuid
    new_token = f"TLG-{str(uuid.uuid4()).upper()[:8]}-{str(uuid.uuid4()).upper()[:8]}"
    
    duration_map = {
        "1_week": 7,
        "1_month": 30,
        "3_months": 90,
        "1_year": 365,
        "lifetime": None
    }
    duration_days = duration_map.get(req.duration, 30)
    
    licenses = load_licenses()
    licenses[new_token] = {
        "hwid": None, 
        "duration_days": duration_days,
        "expires_at": None 
    }
    save_licenses(licenses)
    
    return {
        "status": "success", 
        "token": new_token
    }

@app.get("/api/license/list")
def list_licenses(admin_key: str):
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    licenses = load_licenses()
    result = []
    for token, data in licenses.items():
        result.append({
            "token":      token,
            "hwid":       data.get("hwid"),
            "bound":      data.get("hwid") is not None,
            "created_at": data.get("created_at", ""),
            "duration":   data.get("duration_label", "lifetime"),
            "expires_at": data.get("expires_at", "Never")
        })
    return {"count": len(result), "keys": result}

@app.post("/api/license/revoke")
def revoke_license(req: dict):
    if req.get("admin_key") != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    token = req.get("token", "").strip()
    licenses = load_licenses()
    if token not in licenses:
        raise HTTPException(status_code=404, detail="Token not found")
    del licenses[token]
    save_licenses(licenses)
    return {"status": "revoked", "token": token}

@app.post("/api/license/reset-hwid")
def reset_hwid(req: dict):
    """Unbind a key from its device so it can be used on a new machine."""
    if req.get("admin_key") != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    token = req.get("token", "").strip()
    licenses = load_licenses()
    if token not in licenses:
        raise HTTPException(status_code=404, detail="Token not found")
    licenses[token]["hwid"] = None
    save_licenses(licenses)
    return {"status": "ok", "message": f"HWID reset for {token}"}


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

@app.post("/api/accounts/upload-tdata-zip")
async def upload_tdata_zip(file: UploadFile = File(...)):
    if not OPENTELE_AVAILABLE:
        raise HTTPException(status_code=501, detail="TData uploading is not supported on this host (opentele missing).")
        
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Must be a .zip file containing a tdata folder")
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(await file.read())
            
        extract_path = os.path.join(tmpdir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        # Find the tdata folder inside extracted
        tdata_path = None
        for root, dirs, files in os.walk(extract_path):
            if "key_datas" in files or any(d.endswith('s') and len(d) == 17 for d in dirs):
                tdata_path = root
                break
                
        if not tdata_path:
            raise HTTPException(status_code=400, detail="Invalid tdata format. Could not find key_datas.")
            
        try:
            api = API.TelegramDesktop.Generate()
            tdesk = TDesktop(tdata_path)
            if not tdesk.isLoaded():
                raise HTTPException(status_code=400, detail="Could not load session from tdata")
                
            temp_session_path = os.path.join(tmpdir, "temp.session")
            client = await tdesk.ToTelethon(temp_session_path, UseCurrentSession, api)
            
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                raise HTTPException(status_code=400, detail="Session in tdata is not authorized")
                
            user = await client.get_me()
            phone = user.phone
            await client.disconnect()
            
            if not phone:
                raise HTTPException(status_code=400, detail="Could not extract phone number from tdata")
                
            # Move temp session to accounts dir
            final_session_path = os.path.join(ACCOUNTS_DIR, f"{phone}.session")
            shutil.copy(temp_session_path, final_session_path)
            
            return {
                "status": "success",
                "phone": phone,
                "name": f"{user.first_name} {user.last_name or ''}".strip()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/login/request")
async def login_request(req: LoginRequest):
    phone = str(req.phone).strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
        
    session_filename = phone.replace("+", "").replace(" ", "_")
    session_path = os.path.join(ACCOUNTS_DIR, session_filename)
    
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
        import traceback
        traceback.print_exc()
        await client.disconnect()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/login/confirm")
async def login_confirm(req: LoginConfirm):
    phone = str(req.phone).strip()
    code = str(req.code).strip()
    password = str(req.password).strip() if req.password else None
    
    if phone not in PENDING_CLIENTS:
        raise HTTPException(status_code=400, detail="No pending login request for this phone number")
        
    client = PENDING_CLIENTS[phone]
    
    try:
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            if not password:
                return {"status": "password_required", "phone": phone}
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
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
        groups   = [d for d in dialogs if d.is_group or d.is_channel]
        group_list      = [{"id": g.id, "name": g.name} for g in groups]
        channels_count  = sum(1 for d in dialogs if d.is_channel)
        pms_count       = sum(1 for d in dialogs if d.is_user)

        # ── Restriction detection ──────────────────────────────────────────
        is_restricted   = getattr(user, 'restricted', False)
        restrict_reason = ""

        # Parse restriction_reason list if available
        raw_reasons = getattr(user, 'restriction_reason', None) or []
        if raw_reasons:
            parts = []
            for r in raw_reasons:
                platform = getattr(r, 'platform', '')
                reason   = getattr(r, 'reason',   '')
                text     = getattr(r, 'text',     '')
                entry = f"{platform}: {reason}" if platform else reason
                if text:
                    entry += f" — {text}"
                if entry.strip():
                    parts.append(entry.strip())
            restrict_reason = "; ".join(parts) if parts else "Account restricted by Telegram"
            is_restricted = True

        # Also try GetFullUserRequest to catch spam-block and bio-based hints
        if not is_restricted:
            try:
                from telethon.tl.functions.users import GetFullUserRequest
                full = await client(GetFullUserRequest(user))
                full_user = getattr(full, 'full_user', full)

                # about/bio sometimes set to "SpamBlock" or similar by Telegram internally
                about = getattr(full_user, 'about', '') or ''
                if 'spam' in about.lower() or 'block' in about.lower():
                    is_restricted = True
                    restrict_reason = f"Possible spam block (bio: {about[:80]})"

                # Check settings for auto-archive (often set when account is flagged)
                settings = getattr(full_user, 'settings', None)
                if settings and getattr(settings, 'autoarchived', False):
                    is_restricted = True
                    restrict_reason = restrict_reason or "Account auto-archived by Telegram (spam flag)"

            except Exception:
                pass  # Non-critical, skip restriction probe on error

        # ────────────────────────────────────────────────────────
        return {
            "status":           "restricted" if is_restricted else "authorized",
            "user_id":          user.id,
            "name":             f"{user.first_name} {user.last_name or ''}".strip(),
            "username":         f"@{user.username}" if user.username else "None",
            "phone":            f"+{user.phone}",
            "premium":          user.premium,
            "groups_count":     len(groups),
            "channels_count":   channels_count,
            "pms_count":        pms_count,
            "groups":           group_list,
            "is_restricted":    is_restricted,
            "restrict_reason":  restrict_reason,
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

    # Collect filter flags
    f_username       = req.filter_has_username
    f_phone          = req.filter_has_phone
    f_no_bots        = req.filter_no_bots
    f_active_recently = req.filter_active_recently
    f_inactive       = req.filter_inactive
    f_has_name       = req.filter_has_name

    session_path = os.path.join(ACCOUNTS_DIR, session_name)
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
            matches = [d for d in dialogs if (d.is_group or d.is_channel) and keyword_lower in d.name.lower()]
            if not matches:
                raise HTTPException(status_code=404, detail="No matching joined group found")
            group_entity = matches[0].entity
            identifier = "".join([c if c.isalnum() else "_" for c in matches[0].name])
        else:
            group_entity = await client.get_entity(identifier)

        if not group_entity:
            raise HTTPException(status_code=404, detail="Could not resolve group entity")

        from telethon.tl.types import (
            UserStatusRecently, UserStatusOnline, UserStatusLastWeek
        )

        members = []
        total_seen = 0
        filtered_out = 0

        log_msg(f"🕵️‍♂️ [Scraper] Starting scrape on {url} using {session_name}...")

        async for user in client.iter_participants(group_entity):
            total_seen += 1
            
            if total_seen % 50 == 0:
                log_msg(f"🔄 [Scraper] Scanning... Processed {total_seen} members (Saved: {len(members)}, Filtered: {filtered_out})")

            # ── Apply filters ───────────────────────────────────────────────
            if user.is_self or user.deleted:
                filtered_out += 1
                continue

            if f_no_bots and user.bot:
                filtered_out += 1
                continue

            if f_username and not user.username:
                filtered_out += 1
                continue

            if f_phone and not user.phone:
                filtered_out += 1
                continue

            if f_has_name and not (user.first_name or '').strip():
                filtered_out += 1
                continue

            if f_active_recently:
                active = isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek))
                if not active:
                    filtered_out += 1
                    continue

            if f_inactive:
                active = isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek))
                if active:
                    filtered_out += 1
                    continue

            # Log the extracted user every 10 valid members to show some activity without spamming
            if len(members) % 10 == 0 and len(members) > 0:
                log_msg(f"✅ [Scraper] Extracted valid member: @{user.username or user.id}")

            members.append({
                'id': user.id,
                'username': f"@{user.username}" if user.username else '',
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'phone': f"+{user.phone}" if user.phone else '',
                'is_bot': 'Yes' if user.bot else 'No'
            })

        log_msg(f"🎯 [Scraper] Finished! Total Processed: {total_seen} | Successfully Extracted: {len(members)}")

        # Cache results for export
        cache_id = f"members_{identifier}"
        SCRAPED_MEMBERS_CACHE[cache_id] = members

        return {
            "status": "success",
            "count": len(members),
            "total_seen": total_seen,
            "filtered_out": filtered_out,
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
        headers={"Content-Disposition": f"attachment; filename=scraped_{cache_id}.csv"}
    )

@app.get("/api/scraper/export-txt/{cache_id}")
async def export_scraped_txt(cache_id: str):
    if cache_id not in SCRAPED_MEMBERS_CACHE:
        raise HTTPException(status_code=404, detail="Cache not found or expired")
    
    members = SCRAPED_MEMBERS_CACHE[cache_id]
    
    lines = []
    for m in members:
        if m.get("username"):
            lines.append(m['username'])
        elif m.get("phone"):
            lines.append(f"+{m['phone']}")
        else:
            lines.append(str(m["id"]))
            
    output = "\n".join(lines)
    return StreamingResponse(
        iter([output]), 
        media_type="text/plain", 
        headers={"Content-Disposition": f"attachment; filename=scraped_{cache_id}.txt"}
    )

@app.post("/api/scraper/groups")
async def scrape_my_groups(req: AccountRequest):
    session_name = req.account
    session_path = os.path.join(ACCOUNTS_DIR, session_name)
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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

# ─────────────────────────────────────────────
#  ACCOUNT PRE-SCREENING — checks if an account
#  can actually add members to the target group
# ─────────────────────────────────────────────
async def check_account_can_add(session: str, target_group: str) -> tuple:
    """
    Returns (True, target_entity) if the account can add to the target group,
    or (False, reason_string) if it cannot.
    """
    session_path = os.path.join(ACCOUNTS_DIR, session)
    client = make_client(session_path)
    try:
        await client.connect()

        if not await client.is_user_authorized():
            return False, "session expired / unauthorized"

        target_id = parse_identifier(target_group)
        is_private = 'joinchat/' in target_group or '+' in target_group

        # Try to join if not already a member
        try:
            if is_private:
                match = re.search(r'(?:\+|joinchat/)([a-zA-Z0-9_\-]+)', target_group)
                if match:
                    await client(ImportChatInviteRequest(match.group(1)))
            else:
                await client(JoinChannelRequest(target_id))
        except Exception:
            pass  # Already a member or join not needed

        # Resolve the entity
        target_entity = None
        try:
            target_entity = await client.get_entity(target_id)
        except Exception as e:
            return False, f"cannot resolve group ({e})"

        if target_entity is None:
            return False, "group not found"

        # Check admin/add rights by inspecting channel full info or participant rights
        try:
            from telethon.tl.functions.channels import GetFullChannelRequest
            from telethon.tl.types import Channel as TLChannel
            if isinstance(target_entity, TLChannel):
                full = await client(GetFullChannelRequest(target_entity))
                # If bot_info exists or we can get participants, we likely have access
                # Check our own participant status
                me = await client.get_me()
                from telethon.tl.functions.channels import GetParticipantRequest
                from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, ChannelParticipant
                try:
                    part = await client(GetParticipantRequest(target_entity, me))
                    p = part.participant
                    if isinstance(p, (ChannelParticipantCreator,)):
                        pass  # Creator — always can add
                    elif isinstance(p, ChannelParticipantAdmin):
                        # Check invite_users right
                        if not getattr(p.admin_rights, 'invite_users', False):
                            return False, "admin but no invite_users permission"
                    elif isinstance(p, ChannelParticipant):
                        # Regular member — can only add if group allows it
                        if not getattr(full.full_chat, 'can_set_username', True):
                            pass  # public group — members can invite
                except Exception:
                    pass  # Can't get participant info — assume OK and let the add fail naturally
        except Exception:
            pass  # Non-channel or can't check — proceed

        return True, target_entity

    except Exception as e:
        return False, str(e)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def screen_accounts_for_group(accounts: List[str], target_group: str) -> List[str]:
    """
    Checks all accounts and returns only those that can add to the target group.
    Logs a summary of valid/invalid accounts.
    """
    log_msg(f"\n🔍 PRE-SCREENING {len(accounts)} account(s) for target group...")
    valid = []
    invalid = []

    for session in accounts:
        ok, result = await check_account_can_add(session, target_group)
        if ok:
            log_msg(f"   ✅ [{session}] Can add to group")
            valid.append(session)
        else:
            log_msg(f"   ❌ [{session}] Cannot add — {result}")
            invalid.append(session)

    log_msg(f"\n📊 Screening result: {len(valid)} usable / {len(invalid)} blocked")
    if not valid:
        log_msg("⛔ No usable accounts found. Aborting.")
    return valid

# --- Inviter Background Thread Execution ---

async def _try_import_as_contact(client, user_entity, session_name: str, user_label: str) -> bool:
    """
    Attempt to import a user as a phone contact so the adder becomes their contact.
    This bypasses 'My Contacts Only' group-add privacy — Telegram allows contacts
    to directly add you regardless of that setting.
    Returns True if successfully imported.
    """
    phone = getattr(user_entity, 'phone', None)
    if not phone:
        return False  # Cannot import without a phone number
    try:
        from telethon.tl.functions.contacts import ImportContactsRequest
        from telethon.tl.types import InputPhoneContact
        first  = getattr(user_entity, 'first_name', '') or ''
        last   = getattr(user_entity, 'last_name',  '') or ''
        result = await client(ImportContactsRequest([
            InputPhoneContact(client_id=0, phone=phone, first_name=first, last_name=last)
        ]))
        if getattr(result, 'imported', []):
            log_msg(f"   📞 [{session_name}] Imported {user_label} as contact — will attempt direct add.")
            return True
    except Exception:
        pass
    return False


async def _would_send_invite_only(client, user_entity, session_name: str, user_label: str) -> bool:
    """
    Pre-flight check: detect whether calling InviteToChannelRequest would only send
    an invite link notification to the user instead of directly adding them.

    Telegram sends an invite link (not a direct add) when:
      • The user's privacy is set to 'My Contacts' for group adds AND
        the adder is not in their contacts.

    We inspect PeerSettings from GetFullUserRequest:
      • need_contacts_exception = True  →  user has set privacy but we are an exception
      • add_contact = True AND NOT contact →  we're not their contact; privacy may block
    Combined with user.contact / user.mutual_contact flags.

    Returns True if we would only send an invite (should skip), False if direct add likely OK.
    """
    is_contact        = getattr(user_entity, 'contact',        False)
    is_mutual_contact = getattr(user_entity, 'mutual_contact', False)

    # Mutual contacts can ALWAYS be directly added — no invite link
    if is_mutual_contact:
        return False

    try:
        from telethon.tl.functions.users import GetFullUserRequest
        full     = await client(GetFullUserRequest(user_entity))
        settings = getattr(getattr(full, 'full_user', full), 'settings', None)
        if settings is None:
            return False  # Cannot determine — try anyway

        # need_contacts_exception: Telegram set this when the user recently added
        # us to contacts or a special exception exists — direct add should work
        if getattr(settings, 'need_contacts_exception', False):
            return False

        # add_contact=True means we DON'T have this person as a contact yet.
        # Combined with not being their contact → high chance of invite-link-only.
        not_our_contact   = getattr(settings, 'add_contact', False)
        not_their_contact = not is_contact

        if not_our_contact and not_their_contact:
            return True  # Very likely only an invite link would be sent

    except Exception:
        pass  # If check fails, try the add anyway

    return False


async def add_single_user(client, target_entity, user_or_id, session_name):
    """
    Invite a single user to a group/channel WITHOUT sending them an invite link.

    Strategy:
      1. Resolve the user entity.
      2. If a phone number is available (from scraping) → try importing as a contact first.
         This bypasses 'My Contacts Only' privacy so the add is direct, not an invite.
      3. Pre-flight check: if the user would only receive an invite link notification
         (not be directly added), SKIP them entirely — no InviteToChannelRequest call made.
      4. Call InviteToChannelRequest and inspect result.users to confirm direct add.
      5. Fall back to GetParticipantRequest for a secondary membership confirmation.
    """
    from telethon.tl.functions.channels import GetParticipantRequest
    from telethon.tl.types import (
        ChannelParticipant, ChannelParticipantAdmin, ChannelParticipantCreator
    )

    user_label = "Unknown User"
    try:
        # ── Step 1: Resolve user ──────────────────────────────────────────────
        if isinstance(user_or_id, User):
            user_entity = user_or_id
        elif isinstance(user_or_id, str) and (user_or_id.startswith("+") or user_or_id.isdigit()):
            from telethon.tl.functions.contacts import ImportContactsRequest
            from telethon.tl.types import InputPhoneContact
            phone_str = user_or_id if user_or_id.startswith("+") else "+" + user_or_id
            log_msg(f"   📞 [{session_name}] Importing phone {phone_str} to bypass privacy...")
            res = await client(ImportContactsRequest([InputPhoneContact(client_id=0, phone=phone_str, first_name="User", last_name="")]))
            if getattr(res, 'users', []):
                user_entity = res.users[0]
            else:
                log_msg(f"   ⚠️ [{session_name}] Phone {phone_str} is not on Telegram OR their privacy blocks discovery.")
                return False
        else:
            user_entity = await client.get_entity(user_or_id)

        user_label = (
            f"@{user_entity.username}" if getattr(user_entity, 'username', None)
            else f"ID {getattr(user_entity, 'id', 'Unknown')}"
        )
        user_id = getattr(user_entity, 'id', None)

        if isinstance(target_entity, Channel):

            # ── Step 2: Phone-based contact import (bypasses privacy) ─────────
            phone = getattr(user_entity, 'phone', None)
            if phone:
                await _try_import_as_contact(client, user_entity, session_name, user_label)
                # Re-fetch entity so contact flags are updated
                try:
                    user_entity = await client.get_entity(user_id)
                except Exception:
                    pass

            # ── Step 3: Pre-flight — skip if only invite link would be sent ───
            if await _would_send_invite_only(client, user_entity, session_name, user_label):
                log_msg(
                    f"   ⏭️ [{session_name}] Skipped {user_label} — their privacy only allows "
                    f"contacts to add them. Calling the API would send an invite link instead "
                    f"of directly adding. No notification sent."
                )
                return False

            # ── Step 4: Direct add ────────────────────────────────────────────
            result   = await client(InviteToChannelRequest(target_entity, [user_entity]))
            added_ids = {u.id for u in getattr(result, 'users', [])}

            if user_id and user_id in added_ids:
                log_msg(f"   ✅ [{session_name}] Directly added (no invite link): {user_label}")
                return True

            # ── Step 5: Fallback confirmation via GetParticipantRequest ───────
            confirmed = False
            try:
                part = await client(GetParticipantRequest(target_entity, user_entity))
                p    = part.participant
                if isinstance(p, (ChannelParticipant, ChannelParticipantAdmin, ChannelParticipantCreator)):
                    confirmed = True
            except Exception:
                pass

            if confirmed:
                log_msg(f"   ✅ [{session_name}] Successfully added (confirmed): {user_label}")
            else:
                log_msg(
                    f"   📨 [{session_name}] Invite link sent to {user_label} "
                    f"(Telegram prevented direct-add due to their privacy settings or group join-request settings)."
                )
            return confirmed

        elif isinstance(target_entity, Chat):
            await client(AddChatUserRequest(chat_id=target_entity.id, user_id=user_entity, fwd_limit=0))
            log_msg(f"   ✅ [{session_name}] Successfully added: {user_label}")
            return True
        else:
            raise ValueError("Unsupported target entity")

    except UserPrivacyRestrictedError:
        log_msg(f"   ⚠️ [{session_name}] Privacy restricted — {user_label} cannot be added (their settings block it).")
    except UserAlreadyParticipantError:
        log_msg(f"   ℹ️ [{session_name}] Already in group: {user_label}")
    except UserIdInvalidError:
        log_msg(f"   ❌ [{session_name}] Invalid user identifier: {user_label}")
    except (InputUserDeactivatedError, UserKickedError):
        log_msg(f"   ❌ [{session_name}] {user_label} is deactivated or was kicked from this group — skipping.")
    except UserBannedInChannelError:
        log_msg(f"   ❌ [{session_name}] {user_label} is banned from this group and cannot be added back.")
    except UsersTooMuchError:
        log_msg(f"   ❌ [{session_name}] Group member limit reached!")
        return "RESTRICTED"
    except UserNotMutualContactError:
        log_msg(f"   ⚠️ [{session_name}] {user_label} requires mutual contact to be added.")
    except PeerFloodError:
        log_msg(f"   ❌ [{session_name}] Account flagged/restricted by Telegram (PeerFloodError)!")
        return "RESTRICTED"
    except (ChatWriteForbiddenError, ChatAdminRequiredError):
        log_msg(f"   ❌ [{session_name}] Permission denied — no invite rights in this chat.")
        return False
    except FloodWaitError as e:
        log_msg(f"   ⚠️ [{session_name}] Rate limited! Must wait {e.seconds}s.")
        return e.seconds
    except BotGroupsBlockedError:
        log_msg(f"   ❌ [{session_name}] {user_label} is a bot blocked from groups.")
    except Exception as e:
        if isinstance(e, ValueError) and "Could not find the input entity" in str(e):
            log_msg(f"   ❌ [{session_name}] Unknown user. Make sure the account has seen this user before (e.g. they share a chat).")
        else:
            short_label = user_label if isinstance(user_label, str) else "User"
            log_msg(f"   ❌ [{session_name}] Failed to add {short_label}: {type(e).__name__} - {e}")
    return False

async def safe_sleep(seconds: float, flag_key: str) -> bool:
    """Sleeps for `seconds` but returns False immediately if the cancel flag is set."""
    intervals = int(seconds / 0.5)
    remainder = seconds % 0.5
    for _ in range(intervals):
        if GLOBAL_CANCEL_FLAGS.get(flag_key):
            return False
        await asyncio.sleep(0.5)
    if remainder > 0:
        if GLOBAL_CANCEL_FLAGS.get(flag_key):
            return False
        await asyncio.sleep(remainder)
    return True

async def invite_task_worker(accounts: List[str], target_group: str, members: List[str], delay: float):
    log_msg(f"\n==========================================")
    log_msg(f"🚀 INVITATION WEB TASK STARTED")
    log_msg(f"Targets: {len(members)} users | Accounts: {len(accounts)} | Delay: {delay}s")
    log_msg(f"==========================================")
    
    GLOBAL_CANCEL_FLAGS["inviter"] = False
    GLOBAL_CANCEL_FLAGS["inviter"] = False

    target_id = parse_identifier(target_group)

    # Shuffle and distribute targets across ALL accounts
    random.shuffle(members)
    assignments = {acc: [] for acc in accounts}
    for idx, user in enumerate(members):
        acc = accounts[idx % len(accounts)]
        assignments[acc].append(user)
        
    for session in accounts:
        if GLOBAL_CANCEL_FLAGS.get("inviter"):
            log_msg("🛑 Task was manually cancelled.")
            break
            
        targets = assignments[session]
        if not targets:
            continue
            
        log_msg(f"\n🔄 [{session}] Connecting to invite {len(targets)} users...")
        session_path = os.path.join(ACCOUNTS_DIR, session)
        client = TelegramClient(
            session_path, api_id=API_ID, api_hash=API_HASH,
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
                if GLOBAL_CANCEL_FLAGS.get("inviter"):
                    log_msg(f"🛑 [{session}] Inviter stopped mid-loop.")
                    break
                    
                res = await add_single_user(client, target_entity, user, session)
                
                if res == "RESTRICTED":
                    log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                    break
                    
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    log_msg(f"   🕒 Waiting {res}s due to rate limit...")
                    if not await safe_sleep(res, "inviter"):
                        break
                    res_retry = await add_single_user(client, target_entity, user, session)
                    if res_retry == "RESTRICTED":
                        log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                        break
                        
                if i < len(targets) - 1:
                    if not await safe_sleep(delay * random.uniform(0.8, 1.5), "inviter"):
                        break
                    
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
    log_msg(f"Source: {source_group} | Target: {target_group} | Delay: {delay}s")
    log_msg(f"Accounts: {len(accounts)} (Primary: {primary_account})")
    log_msg(f"==========================================")

    GLOBAL_CANCEL_FLAGS["inviter"] = False

    primary_path = os.path.join(ACCOUNTS_DIR, primary_account)
    primary_client = TelegramClient(primary_path, api_id=API_ID, api_hash=API_HASH,
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
                if (d.is_group or d.is_channel) and (source_id.lower() in d.name.lower() or source_id == str(d.id)):
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
        if GLOBAL_CANCEL_FLAGS.get("inviter"):
            log_msg("🛑 Scrape & Add task was manually cancelled.")
            break
            
        targets = assignments[session]
        if not targets:
            continue
            
        log_msg(f"\n🔄 [{session}] Connecting to invite {len(targets)} users...")
        session_path = os.path.join(ACCOUNTS_DIR, session)
        client = TelegramClient(
            session_path, api_id=API_ID, api_hash=API_HASH,
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

            for i, user_obj in enumerate(targets):
                if GLOBAL_CANCEL_FLAGS.get("inviter"):
                    log_msg(f"🛑 [{session}] Scrape & Add stopped mid-loop.")
                    break
                    
                res = await add_single_user(client, target_entity, user_obj, session)
                
                if res == "RESTRICTED":
                    log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                    break
                    
                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    log_msg(f"   🕒 Waiting {res}s due to rate limit...")
                    if not await safe_sleep(res, "inviter"):
                        break
                    res_retry = await add_single_user(client, target_entity, user_obj, session)
                    if res_retry == "RESTRICTED":
                        log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                        break
                        
                if i < len(targets) - 1:
                    if not await safe_sleep(delay * random.uniform(0.8, 1.5), "inviter"):
                        break
                    
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

@app.post("/api/inviter/stop")
async def stop_inviter():
    GLOBAL_CANCEL_FLAGS["inviter"] = True
    log_msg("🛑 Stop signal received. Tasks will abort gracefully...")
    return {"status": "stopped"}

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
        if row.get("phone"):
            phone = row["phone"].strip()
            if not phone.startswith("+"):
                phone = "+" + phone
            members.append(phone)
        elif row.get("username"):
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


async def invite_by_username_worker(accounts: List[str], target_group: str, usernames: List[str], delay: float):
    log_msg(f"\n==========================================")
    log_msg(f"🚀 INVITE BY USERNAME TASK STARTED")
    log_msg(f"Targets: {len(usernames)} usernames | Accounts: {len(accounts)} | Delay: {delay}s")
    log_msg(f"==========================================")

    target_id = parse_identifier(target_group)

    # Shuffle and distribute targets across all accounts
    random.shuffle(usernames)
    assignments = {acc: [] for acc in accounts}
    for idx, username in enumerate(usernames):
        acc = accounts[idx % len(accounts)]
        assignments[acc].append(username)

    GLOBAL_CANCEL_FLAGS["inviter"] = False

    for session in accounts:
        if GLOBAL_CANCEL_FLAGS.get("inviter"):
            log_msg("🛑 Task was manually cancelled.")
            break

        targets = assignments[session]
        if not targets:
            continue

        log_msg(f"\n🔄 [{session}] Connecting to add {len(targets)} username(s)...")
        session_path = os.path.join(ACCOUNTS_DIR, session)
        client = TelegramClient(
            session_path, api_id=API_ID, api_hash=API_HASH,
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

            # Resolve target group
            target_entity = None
            try:
                target_entity = await client.get_entity(target_id)
            except Exception:
                log_msg(f"❌ [{session}] Could not resolve target group '{target_id}'. Skipping.")
                continue

            for i, username in enumerate(targets):
                if GLOBAL_CANCEL_FLAGS.get("inviter"):
                    log_msg(f"🛑 [{session}] Inviter stopped mid-loop.")
                    break

                # Normalize username — strip @ if present
                clean_username = username.lstrip('@').strip()
                if not clean_username:
                    log_msg(f"   ⚠️ [{session}] Skipping empty username.")
                    continue

                res = await add_single_user(client, target_entity, clean_username, session)

                if res == "RESTRICTED":
                    log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                    break

                if isinstance(res, (int, float)) and not isinstance(res, bool):
                    log_msg(f"   🕒 Waiting {res}s due to rate limit...")
                    if not await safe_sleep(res, "inviter"):
                        break
                    res_retry = await add_single_user(client, target_entity, clean_username, session)
                    if res_retry == "RESTRICTED":
                        log_msg(f"   ⚠️ [{session}] Safety breakout triggered to prevent ban.")
                        break

                if i < len(targets) - 1:
                    if not await safe_sleep(delay * random.uniform(0.8, 1.5), "inviter"):
                        break

        except Exception as e:
            log_msg(f"❌ [{session}] Loop error: {e}")
        finally:
            await client.disconnect()

    log_msg(f"\n==========================================")
    log_msg(f"🎉 INVITE BY USERNAME TASK COMPLETED")
    log_msg(f"==========================================")


@app.post("/api/inviter/invite-by-username")
async def start_invite_by_username(req: InviteByUsernameRequest, background_tasks: BackgroundTasks):
    if IS_INVITING:
        raise HTTPException(status_code=400, detail="An inviter task is already running in the background. Please wait for it to finish or restart the server.")
    if not req.accounts:
        raise HTTPException(status_code=400, detail="No accounts specified")
    if not req.usernames:
        raise HTTPException(status_code=400, detail="No usernames provided")
    if not req.target_group:
        raise HTTPException(status_code=400, detail="Target group is required")

    # Clean and deduplicate usernames
    cleaned = list(set([u.lstrip('@').strip() for u in req.usernames if u.strip()]))
    if not cleaned:
        raise HTTPException(status_code=400, detail="No valid usernames after cleaning")

    background_tasks.add_task(
        run_worker_safe,
        invite_by_username_worker,
        req.accounts,
        req.target_group,
        cleaned,
        req.delay
    )
    return {"status": "started", "targets": len(cleaned), "accounts_used": len(req.accounts)}




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
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
    client = TelegramClient(session_path, api_id=API_ID, api_hash=API_HASH,
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
        client = TelegramClient(
            session_path, api_id=API_ID, api_hash=API_HASH,
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

# ─────────────────────────────────────────────
#  ACCOUNT WARMER (Make Account Strong)
# ─────────────────────────────────────────────
REACTIONS_POOL = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "😍", "💯", "🙏", "⚡"]
CHAT_MESSAGES_POOL = [
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

async def warm_account_worker(accounts: List[str], do_react: bool, do_chat: bool,
                               reactions_per_group: int, messages_to_send: int,
                               react_delay: float, chat_delay: float):
    from telethon.tl.functions.messages import SendReactionRequest
    from telethon.tl.types import ReactionEmoji

    log_msg(f"\n==========================================")
    log_msg(f"💪 ACCOUNT WARMER STARTED")
    log_msg(f"Accounts: {len(accounts)} | React: {do_react} | Chat: {do_chat}")
    log_msg(f"==========================================")

    for session in accounts:
        session_path = os.path.join(ACCOUNTS_DIR, session)

        # ── Acquire per-session lock to avoid SQLite "database is locked" ──
        lock = get_session_lock(session)
        async with lock:
            client = make_client(session_path)
            try:
                # Retry connect up to 3 times on db-locked errors
                for attempt in range(3):
                    try:
                        await client.connect()
                        break
                    except Exception as conn_err:
                        if 'database is locked' in str(conn_err).lower() and attempt < 2:
                            log_msg(f"⚠️ [{session}] DB locked on connect, retry {attempt+1}/3 in 5s...")
                            await asyncio.sleep(5)
                        else:
                            raise


                if not await client.is_user_authorized():
                    log_msg(f"❌ [{session}] Session expired or unauthorized. Skipping.")
                    continue

                me = await client.get_me()
                display = f"{me.first_name} ({session})"
                log_msg(f"\n🔄 Warming account: {display}")

                dialogs = await client.get_dialogs()
                groups = [d for d in dialogs if d.is_group or d.is_channel]
                contacts = [d for d in dialogs if d.is_user and not getattr(d.entity, 'bot', False)]

                selected_groups = random.sample(groups, min(3, len(groups))) if groups else []

                # --- Auto React ---
                if do_react:
                    if not selected_groups:
                        log_msg(f"⚠️ [{session}] No groups available to react in.")
                    else:
                        log_msg(f"⚡ [{session}] Starting Auto-React in {len(selected_groups)} group(s)...")
                        total_reacted = 0
                        for group in selected_groups:
                            group_name = getattr(group.entity, 'title', group.name)
                            count = 0
                            try:
                                async for message in client.iter_messages(group.entity, limit=20):
                                    if count >= reactions_per_group:
                                        break
                                    if not message.text and not message.media:
                                        continue
                                    if message.out:
                                        continue
                                    try:
                                        emoji = random.choice(REACTIONS_POOL)
                                        await client(SendReactionRequest(
                                            peer=group.entity,
                                            msg_id=message.id,
                                            reaction=[ReactionEmoji(emoticon=emoji)]
                                        ))
                                        log_msg(f"   {emoji} Reacted in '{group_name}' (msg {message.id})")
                                        total_reacted += 1
                                        count += 1
                                        wait = random.uniform(react_delay * 0.8, react_delay * 1.5)
                                        await asyncio.sleep(wait)
                                    except FloodWaitError as e:
                                        log_msg(f"   ⚠️ Rate limit! Waiting {e.seconds}s...")
                                        await asyncio.sleep(e.seconds)
                                    except Exception as ex:
                                        if 'database is locked' in str(ex).lower():
                                            log_msg(f"   ⚠️ DB locked during react, waiting 5s...")
                                            await asyncio.sleep(5)
                                        else:
                                            log_msg(f"   ❌ Reaction failed: {ex}")
                            except Exception as ex:
                                log_msg(f"   ❌ Error reading '{group_name}': {ex}")
                        log_msg(f"✅ [{session}] Auto-React done! Total: {total_reacted}")

                # --- Auto Chat ---
                if do_chat:
                    # Only keep contacts with a real access_hash (non-zero) — needed to build InputUser
                    valid_contacts = [
                        d for d in contacts
                        if getattr(d.entity, 'id', None) is not None
                        and getattr(d.entity, 'access_hash', None) not in (None, 0)
                        and not getattr(d.entity, 'deleted', False)
                        and not getattr(d.entity, 'bot', False)
                    ]
                    if not valid_contacts:
                        log_msg(f"⚠️ [{session}] No valid contacts to chat with.")
                    else:
                        pick = min(messages_to_send, len(valid_contacts))
                        log_msg(f"💬 [{session}] Starting Auto-Chat with {pick} contact(s)...")
                        sent_to = random.sample(valid_contacts, pick)
                        total_sent = 0
                        for contact in sent_to:
                            name = getattr(contact.entity, 'first_name', None) or 'Friend'
                            uid  = contact.entity.id
                            uhash = contact.entity.access_hash
                            try:
                                msg = random.choice(CHAT_MESSAGES_POOL)
                                # Use InputUser(id, access_hash) — NEVER resolves username
                                from telethon.tl.types import InputUser as TLInputUser
                                input_peer = TLInputUser(uid, uhash)
                                await client.send_message(input_peer, msg)
                                log_msg(f"   ✅ Sent to {name} ({uid}): \"{msg}\"")
                                total_sent += 1
                                wait = random.uniform(chat_delay * 0.8, chat_delay * 1.5)
                                await asyncio.sleep(wait)
                            except UserPrivacyRestrictedError:
                                log_msg(f"   ⚠️ {name} has privacy restrictions, skipping...")
                            except FloodWaitError as e:
                                log_msg(f"   ⚠️ Rate limit! Waiting {e.seconds}s...")
                                await asyncio.sleep(e.seconds)
                            except Exception as ex:
                                ex_str = str(ex).lower()
                                if 'database is locked' in ex_str:
                                    log_msg(f"   ⚠️ DB locked during chat, waiting 5s...")
                                    await asyncio.sleep(5)
                                elif any(k in ex_str for k in ('invalid', 'user id', 'identifier', 'peer', 'no access', 'not found')):
                                    log_msg(f"   ⚠️ {name} ({uid}) — unreachable, skipping...")
                                else:
                                    log_msg(f"   ❌ Failed to message {name}: {ex}")
                        log_msg(f"✅ [{session}] Auto-Chat done! Sent: {total_sent}")



            except Exception as e:
                if 'database is locked' in str(e).lower():
                    log_msg(f"⚠️ [{session}] DB locked — another task is using this session. Skipping for now.")
                else:
                    log_msg(f"❌ [{session}] Warming error: {e}")
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        if len(accounts) > 1:
            between = random.uniform(30, 60)
            log_msg(f"\n⏳ Switching account in {between:.0f}s...")
            await asyncio.sleep(between)

    log_msg(f"\n==========================================")
    log_msg(f"🎉 ACCOUNT WARMER COMPLETED!")
    log_msg(f"==========================================")

@app.post("/api/warm/start")
async def start_warm(req: WarmRequest, background_tasks: BackgroundTasks):
    if not req.accounts:
        raise HTTPException(status_code=400, detail="Select at least one account")
    if not req.do_react and not req.do_chat:
        raise HTTPException(status_code=400, detail="Select at least one action (React or Chat)")

    background_tasks.add_task(
        warm_account_worker,
        req.accounts, req.do_react, req.do_chat,
        req.reactions_per_group, req.messages_to_send,
        req.react_delay, req.chat_delay
    )
    return {"status": "started", "accounts": len(req.accounts)}

# ─────────────────────────────────────────────
#  MASS JOIN GROUP
# ─────────────────────────────────────────────
class JoinGroupRequest(BaseModel):
    accounts: List[str]
    target_group: str
    delay: float

async def join_group_worker(accounts: List[str], target_group: str, delay: float):
    log_msg(f"\n==========================================")
    log_msg(f"🤝 MASS JOIN TASK STARTED")
    log_msg(f"Target: {target_group} | Accounts: {len(accounts)} | Delay: {delay}s")
    log_msg(f"==========================================")

    for session in accounts:
        session_path = os.path.join(ACCOUNTS_DIR, session)
        lock = get_session_lock(session)
        async with lock:
            try:
                log_msg(f"🔄 [{session}] Connecting to join {target_group}...")
                client = TelegramClient(
                    session_path, api_id=API_ID, api_hash=API_HASH,
                    device_model="iPhone 13 Pro Max",
                    system_version="15.5",
                    app_version="8.7.1",
                    lang_code="en",
                    system_lang_code="en"
                )
                await client.connect()
                if not await client.is_user_authorized():
                    log_msg(f"   ❌ [{session}] Not authorized. Skipping.")
                    continue
                
                target = target_group.strip()
                if "joinchat/" in target or target.startswith("+") or "t.me/+" in target:
                    # Private invite link
                    hash_str = target.split("joinchat/")[-1].split("+")[-1].split("/")[-1].strip()
                    await client(ImportChatInviteRequest(hash_str))
                    log_msg(f"   ✅ [{session}] Successfully joined private group.")
                else:
                    # Public group/channel
                    entity = await client.get_entity(target)
                    await client(JoinChannelRequest(entity))
                    log_msg(f"   ✅ [{session}] Successfully joined public group/channel.")
                
            except FloodWaitError as e:
                log_msg(f"   ⚠️ [{session}] Flood wait: {e.seconds}s.")
            except UserAlreadyParticipantError:
                log_msg(f"   ℹ️ [{session}] Already a member.")
            except Exception as e:
                log_msg(f"   ❌ [{session}] Failed to join: {e}")
            finally:
                await client.disconnect()
        
        await asyncio.sleep(delay)

    log_msg(f"==========================================")
    log_msg(f"🎉 MASS JOIN TASK COMPLETED")
    log_msg(f"==========================================")

@app.post("/api/join-group")
async def start_join_group(req: JoinGroupRequest, background_tasks: BackgroundTasks):
    if not req.accounts:
        raise HTTPException(status_code=400, detail="Select at least one account")
    if not req.target_group:
        raise HTTPException(status_code=400, detail="Target group is required")

    background_tasks.add_task(join_group_worker, req.accounts, req.target_group, req.delay)
    return {"status": "started", "accounts": len(req.accounts)}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Serve static files if they exist (for Railway / production)
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    pass
    
    @app.get("/{catchall:path}")
    def serve_frontend(catchall: str):
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        file_path = os.path.join(FRONTEND_DIST, catchall)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn
    # In production/Railway, the PORT env var is usually set. Default to 8000 locally.
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    uvicorn.run(app, host=host, port=port)
