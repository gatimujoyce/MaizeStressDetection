import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.deps import get_db, get_current_user, require_farmer
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.utils import normalize_ke_phone
from app.models import User, RoleEnum
from app.schemas.auth import (
    UserCreate, UserResponse, Token, UserUpdate, PhoneRequest, ResetPasswordRequest, ChangePasswordRequest,
)
from app.services.auth_codes import aware, check_code, issue_code, send_code

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
MIN_PASSWORD_LENGTH = 8
BAD_CODE = "That code is wrong or has expired. Check the text message, or ask for a new code."


def _check_new_password(password: str):
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters")


@router.post("/register/code", status_code=202)
async def request_register_code(body: PhoneRequest, db: AsyncSession = Depends(get_db)):
    """Step 1 of sign-up: text a 6-digit code to the phone so we know the number is the farmer's."""
    phone = normalize_ke_phone(body.phone)
    if (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")
    code = await issue_code(db, phone, "register")
    if code is None:
        raise HTTPException(status_code=429, detail="A code was sent a moment ago. Wait a minute, then ask again.")
    sent = await send_code(db, phone, "register", code)
    await db.commit()
    if not sent:
        raise HTTPException(status_code=502, detail="We could not send the text message. Check the number and try again.")
    return {"status": "sent"}


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Public registration must not be able to create admin accounts
    if user_in.role == RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered")
    _check_new_password(user_in.password)

    normalized_phone = normalize_ke_phone(user_in.phone)

    result = await db.execute(select(User).where(User.phone == normalized_phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")

    if settings.PHONE_VERIFICATION_REQUIRED:
        valid = await check_code(db, normalized_phone, "register", user_in.code or "")
        await db.commit()  # keeps the count of wrong tries
        if not valid:
            raise HTTPException(status_code=400, detail=BAD_CODE)

    new_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        phone=normalized_phone,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    normalized_phone = normalize_ke_phone(form_data.username)
    result = await db.execute(select(User).where(User.phone == normalized_phone))
    user = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if user and user.locked_until and aware(user.locked_until) > now:
        minutes = int((aware(user.locked_until) - now).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Too many wrong passwords. This account is locked for another {minutes} minute(s). "
                   "You can also use Forgot password.")

    if not user or not verify_password(form_data.password, user.password_hash):
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            locked = user.failed_login_count >= MAX_FAILED_LOGINS
            if locked:
                user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                user.failed_login_count = 0
            await db.commit()
            if locked:
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many wrong passwords. This account is locked for {LOCK_MINUTES} minutes. "
                           "You can also use Forgot password.")
        raise HTTPException(status_code=400, detail="Incorrect phone or password")

    user_id, must_change = str(user.id), bool(user.must_change_password)
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        await db.commit()

    access_token = create_access_token(subject=user_id)
    return {"access_token": access_token, "token_type": "bearer", "must_change_password": must_change}


@router.post("/forgot-password")
async def forgot_password(body: PhoneRequest, db: AsyncSession = Depends(get_db)):
    """Text a reset code. The answer is the same whether or not the number has an account."""
    phone = normalize_ke_phone(body.phone)
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user:
        user_id = user.id
        code = await issue_code(db, phone, "reset")
        if code is not None:
            await send_code(db, phone, "reset", code, user_id=user_id)
        await db.commit()
    return {"status": "sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    _check_new_password(body.new_password)
    phone = normalize_ke_phone(body.phone)
    valid = await check_code(db, phone, "reset", body.code)
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if not valid or user is None:
        await db.commit()  # keeps the count of wrong tries
        raise HTTPException(status_code=400, detail=BAD_CODE)
    user.password_hash = get_password_hash(body.new_password)
    user.must_change_password = False
    user.failed_login_count = 0
    user.locked_until = None
    await db.commit()
    return {"status": "ok"}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Works for everyone, including someone who must replace a temporary password."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Your current password is not right")
    _check_new_password(body.new_password)
    if body.new_password == body.current_password:
        raise HTTPException(status_code=400, detail="Choose a password different from the current one")
    current_user.password_hash = get_password_hash(body.new_password)
    current_user.must_change_password = False
    await db.commit()
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
async def read_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    update_data = user_in.model_dump(exclude_unset=True)
    if "phone" in update_data:
        normalized_phone = normalize_ke_phone(update_data["phone"])
        
        if normalized_phone != current_user.phone:
            # Check for conflict
            result = await db.execute(select(User).where(User.phone == normalized_phone))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Phone already registered")
        
        update_data["phone"] = normalized_phone

    for k, v in update_data.items():
        setattr(current_user, k, v)
        
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
