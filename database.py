"""
database.py
===========
SQLAlchemy ORM layer for the TG-Adder web server.

Supports PostgreSQL (preferred) and falls back gracefully when no
DATABASE_URL / DB_* environment variables are supplied.

Environment variables (any one set is enough):
    DATABASE_URL  – full PostgreSQL connection string (Render injects this)
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME – individual parts
"""

import os
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# ---------------------------------------------------------------------------
# Connection setup
# ---------------------------------------------------------------------------

_DB_USER     = os.getenv("DB_USER")
_DB_PASSWORD = os.getenv("DB_PASSWORD")
_DB_HOST     = os.getenv("DB_HOST", "localhost")
_DB_PORT     = os.getenv("DB_PORT", "5432")
_DB_NAME     = os.getenv("DB_NAME")

if _DB_USER and _DB_NAME:
    DATABASE_URL = (
        f"postgresql://{_DB_USER}:{_DB_PASSWORD}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
    )
else:
    DATABASE_URL = os.getenv("DATABASE_URL")

# Render sometimes provides the legacy "postgres://" scheme
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Detect whether we are connecting to a remote host (Render) or localhost
# Only enforce SSL for remote connections — local PostgreSQL does not support it
_is_remote = DATABASE_URL and "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL

if _is_remote and DATABASE_URL and "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

_SSL_ARGS = {"sslmode": "require"} if _is_remote else {}

engine = (
    create_engine(
        DATABASE_URL,
        connect_args=_SSL_ARGS,
        pool_pre_ping=True,       # drops stale connections before use
        pool_size=5,              # keep pool small on free tier
        max_overflow=10,
        pool_recycle=300,         # recycle connections every 5 min to avoid EOF
        pool_timeout=30,
    )
    if DATABASE_URL
    else None
)
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)
Base = declarative_base()

# Global write lock – ensures thread-safe access for both reads and writes
_db_lock = threading.Lock()

# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class License(Base):
    """Desktop-client license tokens."""
    __tablename__ = "licenses"

    token          = Column(String, primary_key=True, index=True)
    hwid           = Column(String, nullable=True)
    bound          = Column(Boolean, default=False)
    duration_days  = Column(Integer, nullable=True)
    expires_at     = Column(String, nullable=True)
    computer_model = Column(String, nullable=True)
    last_ip        = Column(String, nullable=True)
    label          = Column(String, nullable=True)


class WebUser(Base):
    """Web-dashboard user accounts."""
    __tablename__ = "web_users"

    username    = Column(String, primary_key=True, index=True)
    password    = Column(String, nullable=True)
    license_key = Column(String, nullable=True)
    created_at  = Column(String, nullable=True)


class TelegramAccount(Base):
    """Telegram sessions linked to a web user."""
    __tablename__ = "telegram_accounts"

    phone_number     = Column(String, primary_key=True, index=True)
    session_filename = Column(String, nullable=False)
    web_username     = Column(String, nullable=False, index=True)
    created_at       = Column(String, nullable=True)


# Create tables on first startup (no-op if they already exist)
if engine:
    Base.metadata.create_all(bind=engine)

# Public API surface
__all__ = [
    "engine",
    "db_load_licenses",
    "db_save_licenses",
    "db_load_web_users",
    "db_save_web_users",
    "db_add_telegram_account",
    "db_get_user_accounts",
    "db_delete_telegram_account",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_engine():
    """Raise RuntimeError if no database engine is configured."""
    if not engine:
        raise RuntimeError("No DATABASE_URL configured – database is unavailable.")


# ---------------------------------------------------------------------------
# License CRUD
# ---------------------------------------------------------------------------

def db_load_licenses() -> dict:
    """Return all licenses as a dict keyed by token."""
    if not engine:
        return {}
    with _db_lock:
        db = SessionLocal()
        try:
            rows = db.query(License).all()
            return {
                lic.token: {
                    "hwid":           lic.hwid,
                    "bound":          lic.bound,
                    "duration_days":  lic.duration_days,
                    "expires_at":     lic.expires_at,
                    "computer_model": lic.computer_model,
                    "last_ip":        lic.last_ip,
                    "label":          lic.label,
                }
                for lic in rows
            }
        finally:
            db.close()


def db_save_licenses(data: dict) -> None:
    """Upsert licenses and remove any that are no longer in *data*."""
    if not engine:
        return
    with _db_lock:
        db = SessionLocal()
        try:
            for token, details in data.items():
                lic = db.query(License).filter(License.token == token).first()
                if not lic:
                    lic = License(token=token)
                    db.add(lic)
                lic.hwid           = details.get("hwid")
                lic.bound          = details.get("bound", False)
                lic.duration_days  = details.get("duration_days")
                lic.expires_at     = details.get("expires_at")
                lic.computer_model = details.get("computer_model")
                lic.last_ip        = details.get("last_ip")
                lic.label          = details.get("label")

            if data:
                db.query(License).filter(
                    License.token.notin_(list(data.keys()))
                ).delete(synchronize_session=False)
            else:
                db.query(License).delete(synchronize_session=False)

            db.commit()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Web-user CRUD
# ---------------------------------------------------------------------------

def db_load_web_users() -> dict:
    """Return all web users as a dict keyed by username."""
    if not engine:
        return {}
    with _db_lock:
        db = SessionLocal()
        try:
            rows = db.query(WebUser).all()
            return {
                u.username: {
                    "password":    u.password,
                    "license_key": u.license_key,
                    "created_at":  u.created_at,
                }
                for u in rows
            }
        finally:
            db.close()


def db_save_web_users(data: dict) -> None:
    """Upsert web users and remove any that are no longer in *data*."""
    if not engine:
        return
    with _db_lock:
        db = SessionLocal()
        try:
            for username, details in data.items():
                user = db.query(WebUser).filter(WebUser.username == username).first()
                if not user:
                    user = WebUser(username=username)
                    db.add(user)
                user.password    = details.get("password")
                user.license_key = details.get("license_key")
                user.created_at  = details.get("created_at")

            if data:
                db.query(WebUser).filter(
                    WebUser.username.notin_(list(data.keys()))
                ).delete(synchronize_session=False)
            else:
                db.query(WebUser).delete(synchronize_session=False)

            db.commit()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Telegram-account CRUD
# ---------------------------------------------------------------------------

def db_add_telegram_account(
    phone_number: str,
    session_filename: str,
    web_username: str,
) -> None:
    """Insert or update a Telegram account linked to *web_username*."""
    if not engine:
        return
    with _db_lock:
        db = SessionLocal()
        try:
            account = (
                db.query(TelegramAccount)
                .filter(TelegramAccount.phone_number == phone_number)
                .first()
            )
            if not account:
                account = TelegramAccount(phone_number=phone_number)
                db.add(account)

            # Normalise session filename
            if not session_filename.endswith(".session"):
                session_filename = f"{session_filename}.session"

            account.session_filename = session_filename
            account.web_username     = web_username
            account.created_at       = datetime.now(timezone.utc).isoformat()
            db.commit()
        finally:
            db.close()


def db_get_user_accounts(web_username: str) -> list:
    """Return all Telegram accounts belonging to *web_username*."""
    if not engine:
        return []
    with _db_lock:
        db = SessionLocal()
        try:
            rows = (
                db.query(TelegramAccount)
                .filter(TelegramAccount.web_username == web_username)
                .all()
            )
            return [
                {
                    "phone":            a.phone_number,
                    "session_filename": a.session_filename,
                    "created_at":       a.created_at,
                }
                for a in rows
            ]
        finally:
            db.close()


def db_delete_telegram_account(phone_number: str, web_username: str) -> bool:
    """Delete a Telegram account. Returns True if found and deleted."""
    if not engine:
        return False
    with _db_lock:
        db = SessionLocal()
        try:
            acc = (
                db.query(TelegramAccount)
                .filter(
                    TelegramAccount.phone_number == phone_number,
                    TelegramAccount.web_username == web_username,
                )
                .first()
            )
            if acc:
                db.delete(acc)
                db.commit()
                return True
            return False
        finally:
            db.close()
