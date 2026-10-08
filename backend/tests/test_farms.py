import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
import uuid
from app.routers.farms import read_farms, read_farm, update_farm, delete_farm
from app.models import User, Farm

@pytest.mark.asyncio
async def test_read_farms_only_own():
    mock_db = AsyncMock()
    current_user_id = uuid.uuid4()
    
    # Mock finding 2 farms
    f1 = Farm(id=uuid.uuid4(), user_id=current_user_id, name="F1")
    f2 = Farm(id=uuid.uuid4(), user_id=current_user_id, name="F2")
    
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [f1, f2]
    mock_db.execute.return_value = mock_result
    
    current_user = User(id=current_user_id)
    res = await read_farms(current_user=current_user, db=mock_db)
    
    assert len(res) == 2
    query = mock_db.execute.call_args[0][0]
    params = dict(query.compile().params)
    assert current_user_id in params.values()

@pytest.mark.asyncio
async def test_user_a_cannot_read_user_b_farm():
    mock_db = AsyncMock()
    current_user = User(id=uuid.uuid4())
    farm_id = uuid.uuid4()
    
    # Simulate DB returning None because the user_id condition failed
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await read_farm(id=farm_id, current_user=current_user, db=mock_db)
        
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_user_a_cannot_delete_user_b_farm():
    mock_db = AsyncMock()
    current_user = User(id=uuid.uuid4())
    farm_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc:
        await delete_farm(id=farm_id, current_user=current_user, db=mock_db)
        
    assert exc.value.status_code == 404
