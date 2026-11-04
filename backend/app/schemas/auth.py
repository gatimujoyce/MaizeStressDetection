from pydantic import BaseModel
from typing import Optional
from app.models import RoleEnum
import uuid

class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    role: Optional[RoleEnum] = RoleEnum.farmer
    code: Optional[str] = None  # the 6-digit code texted to the phone

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    role: RoleEnum
    must_change_password: bool = False
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str
    must_change_password: bool = False

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class PhoneRequest(BaseModel):
    phone: str

class ResetPasswordRequest(BaseModel):
    phone: str
    code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
