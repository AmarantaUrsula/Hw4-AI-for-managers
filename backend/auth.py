"""Create account / log in (Problem 4).

Passwords
- Hashed with PBKDF2-HMAC-SHA256, 120,000 iterations, a fresh random salt per
  user, stored as pbkdf2_sha256$<salt>$<hex digest> (same format as the seed
  test user). The plain password is never stored, logged, or returned.
- Login re-hashes the typed password with the stored salt and compares the
  digests in constant time (hmac.compare_digest).

Sessions
- On success the server sets an HttpOnly cookie holding "<user_id>.<expiry>.<HMAC>".
  JavaScript (and therefore an injected script or a chatbot) cannot read it,
  and it cannot be forged without the server secret in backend/.session_secret.

No endpoint ever returns password_hash.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from db import connect

SECRET_PATH = Path(__file__).resolve().parent / ".session_secret"

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
MIN_PASSWORD_LEN = 8
SESSION_COOKIE = "cc_session"
SESSION_SECONDS = 7 * 24 * 3600

# Simple brute-force guard: max failed logins per email in a rolling window.
MAX_FAILED = 5
FAILED_WINDOW = 15 * 60
_failed: dict[str, list[float]] = defaultdict(list)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- password hashing ----------

def _pbkdf2_hex(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()


def hash_password(password: str) -> str:
    """Create account only: the one place a new salt is generated."""
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${salt}${_pbkdf2_hex(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Log in: reuse the salt read from the stored string (the middle piece); never make a new one."""
    try:
        algorithm, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM or not salt or not digest:
        return False
    return hmac.compare_digest(_pbkdf2_hex(password, salt), digest)


# A real hash to compare against when the email doesn't exist, so a wrong email
# takes as long as a wrong password (no account enumeration by timing).
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- sessions ----------

def _secret() -> bytes:
    if not SECRET_PATH.exists():
        SECRET_PATH.write_text(secrets.token_hex(32))
        os.chmod(SECRET_PATH, 0o600)
    return SECRET_PATH.read_text().strip().encode()


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_SECONDS}"
    return f"{payload}.{_sign(payload)}"


def read_session(token: str | None) -> int | None:
    if not token:
        return None
    try:
        user_id, expires, sig = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(f"{user_id}.{expires}")):
        return None
    if int(expires) < time.time():
        return None
    return int(user_id)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session(user_id),
        max_age=SESSION_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,  # localhost is plain http; set True behind HTTPS
    )


# ---------- database ----------

def _connect(write: bool = False) -> sqlite3.Connection:
    # Working copy only (data/campus_customs_new.db); the original is never opened.
    return connect(write)


def public_user(row: sqlite3.Row) -> dict:
    # The only user fields that ever leave the server. Never password_hash.
    return {
        "id": row["id"],
        "first_name": row["first_name"] or row["name"].split(" ")[0],
        "last_name": row["last_name"] or " ".join(row["name"].split(" ")[1:]),
        "name": row["name"],
        "email": row["email"],
    }


def current_user(request: Request) -> dict | None:
    user_id = read_session(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return public_user(row) if row else None


# ---------- endpoints ----------

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup", status_code=201)
def signup(req: SignupRequest, response: Response) -> dict:
    first = req.first_name.strip()
    last = req.last_name.strip()
    email = req.email.strip().lower()
    if not first or not last:
        raise HTTPException(400, "Please enter your first and last name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if len(req.password) < MIN_PASSWORD_LEN:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    if req.password != req.confirm_password:
        raise HTTPException(400, "Passwords do not match.")

    with _connect(write=True) as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(409, "An account with this email already exists. Try logging in.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, hash_password(req.password), first, last),
        )
        row = conn.execute(
            "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    set_session_cookie(response, row["id"])
    return {"user": public_user(row)}


@router.post("/login")
def login(req: LoginRequest, response: Response) -> dict:
    email = req.email.strip().lower()
    now = time.time()
    _failed[email] = [t for t in _failed[email] if now - t < FAILED_WINDOW]
    if len(_failed[email]) >= MAX_FAILED:
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    with _connect() as conn:
        row = conn.execute(
            "SELECT id, name, email, first_name, last_name, password_hash FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()

    ok = verify_password(req.password, row["password_hash"] if row else _DUMMY_HASH)
    if not row or not ok:
        _failed[email].append(now)
        # Same message for wrong email and wrong password.
        raise HTTPException(401, "Incorrect email or password.")

    _failed.pop(email, None)
    set_session_cookie(response, row["id"])
    return {"user": public_user(row)}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(request: Request) -> dict:
    return {"user": current_user(request)}
