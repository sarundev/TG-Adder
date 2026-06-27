from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

if DB_USER and DB_NAME:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class License(Base):
    __tablename__ = "licenses"
    token = Column(String, primary_key=True, index=True)
    hwid = Column(String, nullable=True)
    bound = Column(Boolean, default=False)
    duration_days = Column(Integer, nullable=True)
    expires_at = Column(String, nullable=True)
    computer_model = Column(String, nullable=True)
    last_ip = Column(String, nullable=True)
    label = Column(String, nullable=True)

class WebUser(Base):
    __tablename__ = "web_users"
    username = Column(String, primary_key=True, index=True)
    password = Column(String, nullable=True)
    license_key = Column(String, nullable=True)
    created_at = Column(String, nullable=True)

class TelegramAccount(Base):
    __tablename__ = "telegram_accounts"
    phone_number = Column(String, primary_key=True, index=True)
    session_filename = Column(String, nullable=False)
    web_username = Column(String, nullable=False, index=True)
    created_at = Column(String, nullable=True)

if engine:
    Base.metadata.create_all(bind=engine)

def db_load_licenses():
    db = SessionLocal()
    try:
        licenses = db.query(License).all()
        result = {}
        for lic in licenses:
            result[lic.token] = {
                "hwid": lic.hwid,
                "bound": lic.bound,
                "duration_days": lic.duration_days,
                "expires_at": lic.expires_at,
                "computer_model": lic.computer_model,
                "last_ip": lic.last_ip,
                "label": lic.label
            }
        return result
    finally:
        db.close()

def db_save_licenses(data):
    db = SessionLocal()
    try:
        for token, details in data.items():
            lic = db.query(License).filter(License.token == token).first()
            if not lic:
                lic = License(token=token)
                db.add(lic)
            lic.hwid = details.get("hwid")
            lic.bound = details.get("bound", False)
            lic.duration_days = details.get("duration_days")
            lic.expires_at = details.get("expires_at")
            lic.computer_model = details.get("computer_model")
            lic.last_ip = details.get("last_ip")
            lic.label = details.get("label")
        
        # Remove licenses that are no longer in the data
        if data:
            db.query(License).filter(License.token.notin_(list(data.keys()))).delete(synchronize_session=False)
        else:
            db.query(License).delete(synchronize_session=False)
        
        db.commit()
    finally:
        db.close()

def db_load_web_users():
    db = SessionLocal()
    try:
        users = db.query(WebUser).all()
        result = {}
        for u in users:
            result[u.username] = {
                "password": u.password,
                "license_key": u.license_key,
                "created_at": u.created_at
            }
        return result
    finally:
        db.close()

def db_save_web_users(data):
    db = SessionLocal()
    try:
        for username, details in data.items():
            user = db.query(WebUser).filter(WebUser.username == username).first()
            if not user:
                user = WebUser(username=username)
                db.add(user)
            user.password = details.get("password")
            user.license_key = details.get("license_key")
            user.created_at = details.get("created_at")
            
        if data:
            db.query(WebUser).filter(WebUser.username.notin_(list(data.keys()))).delete(synchronize_session=False)
        else:
            db.query(WebUser).delete(synchronize_session=False)
            
        db.commit()
    finally:
        db.close()

def db_add_telegram_account(phone_number, session_filename, web_username):
    if not engine: return
    db = SessionLocal()
    try:
        from datetime import datetime, timezone
        account = db.query(TelegramAccount).filter(TelegramAccount.phone_number == phone_number).first()
        if not account:
            account = TelegramAccount(phone_number=phone_number)
            db.add(account)
        account.session_filename = session_filename
        account.web_username = web_username
        account.created_at = datetime.now(timezone.utc).isoformat()
        db.commit()
    finally:
        db.close()

def db_get_user_accounts(web_username):
    if not engine: return []
    db = SessionLocal()
    try:
        accounts = db.query(TelegramAccount).filter(TelegramAccount.web_username == web_username).all()
        return [{"phone": a.phone_number, "session_filename": a.session_filename} for a in accounts]
    finally:
        db.close()
