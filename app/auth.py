"""Session signing (HMAC-SHA256) and magic-link token management."""
import base64
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import ForumSettings, LoginToken, Member

TOKEN_EXPIRY_MINUTES = 15
SESSION_DAYS = 30


# ---------- Session secret ----------

def _get_or_generate_secret(db: Session) -> str:
    """Return the session signing secret. If none exists yet, generate one
    and persist it to forum_settings so all workers (and restarts) agree."""
    from app.branding import get_or_create_settings
    settings = get_or_create_settings(db)
    if settings.session_secret:
        return settings.session_secret
    new_secret = secrets.token_hex(32)
    settings.session_secret = new_secret
    db.commit()
    return new_secret


# ---------- Session cookie ----------

def sign_session(email: str, secret: str) -> str:
    expires = int(time.time()) + SESSION_DAYS * 86400
    email_b64 = base64.urlsafe_b64encode(email.encode()).decode().rstrip("=")
    payload = f"{email_b64}.{expires}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return f"{payload}.{sig_b64}"


def verify_session(token: str, secret: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        email_b64, expires_s, sig_b64 = parts
        if int(expires_s) < time.time():
            return None
        expected_payload = f"{email_b64}.{expires_s}"
        expected_sig = hmac.new(secret.encode(), expected_payload.encode(), hashlib.sha256).digest()
        given_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
        if not hmac.compare_digest(expected_sig, given_sig):
            return None
        email = base64.urlsafe_b64decode(email_b64 + "=" * (-len(email_b64) % 4)).decode()
        return email
    except Exception:
        return None


# ---------- Magic-link tokens ----------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_login_token(db: Session, email: str, requester_ip: str = "") -> str:
    """Generate a one-use magic-link token. Returns the raw token (to embed
    in the email link). The DB only stores the SHA-256 hash."""
    token = secrets.token_urlsafe(32)
    lt = LoginToken(
        email=email.lower().strip(),
        token_hash=_hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        requester_ip=requester_ip,
    )
    db.add(lt)
    db.commit()
    return token


def consume_login_token(db: Session, raw_token: str) -> str | None:
    """Validate a token. Returns the email if valid (and marks it consumed),
    or None if expired / already used / not found."""
    h = _hash_token(raw_token)
    lt = db.query(LoginToken).filter_by(token_hash=h).one_or_none()
    if lt is None:
        return None
    if lt.consumed_at is not None:
        return None
    if lt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    lt.consumed_at = datetime.now(timezone.utc)
    db.commit()
    return lt.email


def is_member_email(db: Session, email: str) -> bool:
    return db.query(Member).filter_by(email=email.lower().strip()).one_or_none() is not None


# ---------- Rate limiting (in-memory, per-process) ----------

_REQUEST_LOG: dict[str, list[float]] = {}
MAX_REQUESTS = 5
WINDOW_SECS = 3600


def rate_limit_ok(email: str) -> bool:
    email = email.lower().strip()
    now = time.time()
    timestamps = _REQUEST_LOG.get(email, [])
    timestamps = [t for t in timestamps if now - t < WINDOW_SECS]
    if len(timestamps) >= MAX_REQUESTS:
        return False
    timestamps.append(now)
    _REQUEST_LOG[email] = timestamps
    return True
