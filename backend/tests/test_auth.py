import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import uuid
from app.routers.auth import register, login, update_profile
from app.schemas.auth import UserCreate, UserUpdate
from app.models import User, RoleEnum
from fastapi.security import OAuth2PasswordRequestForm

@pytest.mark.asyncio
async def test_register_duplicate_phone_across_formats():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User() # Simulating existing user
    mock_db.execute.return_value = mock_result

    user_in = UserCreate(name="Test", phone="0712345678", password="pw", role=RoleEnum.farmer)
    
    with pytest.raises(HTTPException) as exc:
        await register(user_in, db=mock_db)
    
    assert exc.value.status_code == 400
    assert exc.value.detail == "Phone already registered"
    
    # Check that it actually queried for normalized format
    query = mock_db.execute.call_args[0][0]
    params = dict(query.compile().params)
    assert "+254712345678" in params.values()

@pytest.mark.asyncio
async def test_login_cross_format():
    mock_db = AsyncMock()
    user = User(id=uuid.uuid4(), password_hash="hashed")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user 
    mock_db.execute.return_value = mock_result

    form_data = OAuth2PasswordRequestForm(username="0712345678", password="pw") # input uses '0' prefix
    
    with patch("app.routers.auth.verify_password", return_value=True), \
         patch("app.routers.auth.create_access_token", return_value="token"):
        res = await login(form_data, db=mock_db)
        
    assert res["access_token"] == "token"
    # Verify the cross-format check happened
    query = mock_db.execute.call_args[0][0]
    params = dict(query.compile().params)
    assert "+254712345678" in params.values()

@pytest.mark.asyncio
async def test_update_profile_duplicate_phone():
    mock_db = AsyncMock()
    current_user = User(id=uuid.uuid4(), phone="+254799999999")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = User() # Conflict found
    mock_db.execute.return_value = mock_result

    update_in = UserUpdate(phone="0711111111")
    
    with pytest.raises(HTTPException) as exc:
        await update_profile(update_in, current_user=current_user, db=mock_db)
        
    assert exc.value.status_code == 400
    assert exc.value.detail == "Phone already registered"
