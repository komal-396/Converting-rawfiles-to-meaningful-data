"""Simple local account system: username/password login + per-user saved quest progress.

No external auth service — credentials and progress are stored as local JSON files.
Good enough for a local/demo tool; swap for a real identity provider before any
multi-machine or production deployment.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from core.config import USERS_DIR, USERS_FILE


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()


def register_user(username: str, password: str) -> Optional[str]:
    """Create a new account. Returns an error message, or None on success."""
    username = username.strip().lower()
    if not username or not password:
        return "Username and password are required."
    if len(password) < 4:
        return "Password must be at least 4 characters."
    users = _load_users()
    if username in users:
        return "That username is already taken."
    salt = os.urandom(16)
    users[username] = {"salt": salt.hex(), "hash": _hash_password(password, salt)}
    _save_users(users)
    return None


def verify_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    users = _load_users()
    record = users.get(username)
    if not record:
        return False
    salt = bytes.fromhex(record["salt"])
    return _hash_password(password, salt) == record["hash"]


def _progress_path(username: str) -> Path:
    return USERS_DIR / f"{username.strip().lower()}_progress.json"


def load_progress(username: str) -> dict:
    """Load this user's saved quest state (XP, badges, current run). Empty dict if none yet."""
    path = _progress_path(username)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_progress(username: str, progress: dict) -> None:
    """Persist this user's quest state so it's there next time they log in."""
    _progress_path(username).write_text(json.dumps(progress, indent=2, default=str), encoding="utf-8")
