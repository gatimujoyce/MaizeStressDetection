"""One-time SMS codes (phone check at sign-up, forgot password) and temporary passwords.

Only a keyed hash of each code is stored. A code works once, expires after 10 minutes, and allows 5 wrong tries."""
import asyncio
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.models import OneTimeCode
from app.services.sms import send_sms
from app.services.sms_log import record_sms

CODE_MINUTES = 10
MAX_WRONG_TRIES = 5
RESEND_SECONDS = 60
MAX_CODES_PER_HOUR = 5
# No 0/O, 1/l/I: easier to read off a phone screen.
TEMP_PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def aware(moment):
    """Databases may hand back times without a zone; treat those as UTC."""
    if moment is not None and moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def make_code() -> str:
    return f"{secrets.randbelow(10 ** 6):06d}"


def make_temp_password() -> str:
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(10))


def hash_code(purpose: str, phone: str, code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"{purpose}:{phone}:{code}".encode(), hashlib.sha256).hexdigest()


async def issue_code(db, phone: str, purpose: str):
    """Make a new code for this phone and purpose. Returns the code, or None when asked for too often.
    The caller commits."""
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(OneTimeCode).where(OneTimeCode.phone == phone, OneTimeCode.purpose == purpose,
                                  OneTimeCode.created_at > now - timedelta(hours=1))
    )).scalars().all()
    if len(rows) >= MAX_CODES_PER_HOUR:
        return None
    if any(aware(row.created_at) > now - timedelta(seconds=RESEND_SECONDS) for row in rows):
        return None
    for row in rows:
        row.used = True  # an older code stops working once a new one is sent
    code = make_code()
    db.add(OneTimeCode(phone=phone, purpose=purpose, code_hash=hash_code(purpose, phone, code),
                       created_at=now, expires_at=now + timedelta(minutes=CODE_MINUTES)))
    return code


async def check_code(db, phone: str, purpose: str, code: str) -> bool:
    """True when the code is right (and uses it up). A wrong guess is counted. The caller must commit either way."""
    now = datetime.now(timezone.utc)
    code = (code or "").strip()
    row = (await db.execute(
        select(OneTimeCode).where(OneTimeCode.phone == phone, OneTimeCode.purpose == purpose, OneTimeCode.used.is_(False))
        .order_by(OneTimeCode.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if row is None or aware(row.expires_at) < now or row.attempts >= MAX_WRONG_TRIES:
        return False
    if hmac.compare_digest(row.code_hash, hash_code(purpose, phone, code)):
        row.used = True
        return True
    row.attempts += 1
    return False


async def send_code(db, phone: str, purpose: str, code: str, user_id=None) -> bool:
    """Text the code and add a log row (the code itself is not kept in the log). The caller commits."""
    sent = await asyncio.to_thread(
        send_sms, phone, f"Your MaizeStressMonitor code is {code}. It works for {CODE_MINUTES} minutes. Do not share it.")
    if settings.AUTH_LOG_CODES:
        print(f"[auth] {purpose} code for {phone}: {code}")  # testing only; leave AUTH_LOG_CODES off in real use
    record_sms(db, user_id=user_id, farm_id=None, alert_id=None, kind="verification_code", phone=phone,
               message="Verification code sent (hidden)", status="sent" if sent else "failed", result=sent)
    return sent
