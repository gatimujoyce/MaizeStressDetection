from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
import uuid

from app.core.deps import get_db
from app.schemas.auth import UserCreate, UserResponse, Token
from app.models import User, RoleEnum
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Public registration must not be able to create admin accounts
    if user_in.role == RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered")

    result = await db.execute(select(User).where(User.phone == user_in.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    new_user = User(
        id=uuid.uuid4(),
        name=user_in.name,
        phone=user_in.phone,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect phone or password")
    
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
