from pydantic import BaseModel
from typing import Optional
from app.models import RoleEnum
import uuid

class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    role: Optional[RoleEnum] = RoleEnum.farmer

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    role: RoleEnum
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
