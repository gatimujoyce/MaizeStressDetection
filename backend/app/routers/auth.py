from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
import uuid

from app.core.deps import get_db, require_farmer
from app.schemas.auth import UserCreate, UserResponse, Token, UserUpdate
from app.models import User, RoleEnum
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.utils import normalize_ke_phone

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Public registration must not be able to create admin accounts
    if user_in.role == RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered")

    normalized_phone = normalize_ke_phone(user_in.phone)

    result = await db.execute(select(User).where(User.phone == normalized_phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")
    
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
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect phone or password")
    
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}

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
        
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for k, v in update_data.items():
        setattr(current_user, k, v)
        
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
