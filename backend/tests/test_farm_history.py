import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models import Checkin, Farm, Prediction, RoleEnum, SensorReading, User
from app.routers.farms import get_farm_history


def _scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _collection_result(values):
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


def _user(user_id, role=RoleEnum.farmer):
    return User(
        id=user_id,
        name="Test User",
        phone=str(user_id),
        password_hash="hash",
        role=role,
    )


def _farm(farm_id, owner_id):
    return Farm(
        id=farm_id,
        user_id=owner_id,
        name="Test Farm",
        location="Here",
        soil_type="loam",
    )


@pytest.mark.asyncio
async def test_farm_history_returns_all_collections():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=farm_id,
        soil_moisture=0.4,
        temperature=25.0,
        humidity=60.0,
        leaf_wetness=2.0,
        recorded_at=now,
        source="simulated",
    )
    checkin = Checkin(
        id=uuid.uuid4(),
        farm_id=farm_id,
        image_path="uploads/leaf.jpg",
        created_at=now,
    )
    prediction = Prediction(
        id=uuid.uuid4(),
        checkin_id=checkin.id,
        reading_id=reading.id,
        triage_result="in_scope",
        severity="High",
        model_versions={"disease": "v1"},
        created_at=now,
    )
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_result(_farm(farm_id, owner_id)),
        _collection_result([reading]),
        _collection_result([checkin]),
        _collection_result([prediction]),
    ])

    response = await get_farm_history(
        farm_id,
        _user(owner_id),
        db,
        limit=100,
        offset=0,
    )

    assert response.farm_id == farm_id
    assert [item.id for item in response.readings] == [reading.id]
    assert [item.id for item in response.checkins] == [checkin.id]
    assert [item.id for item in response.predictions] == [prediction.id]
    assert response.predictions[0].checkin_id == checkin.id
    assert response.predictions[0].reading_id == reading.id
    assert len(db.execute.await_args_list) == 4


@pytest.mark.asyncio
async def test_farm_history_returns_empty_collections_when_no_history():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_result(_farm(farm_id, owner_id)),
        _collection_result([]),
        _collection_result([]),
        _collection_result([]),
    ])

    response = await get_farm_history(
        farm_id,
        _user(owner_id),
        db,
        limit=100,
        offset=0,
    )

    assert response.farm_id == farm_id
    assert response.readings == []
    assert response.checkins == []
    assert response.predictions == []


@pytest.mark.asyncio
async def test_farm_history_returns_404_for_missing_farm():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(None))

    with pytest.raises(HTTPException) as exc_info:
        await get_farm_history(uuid.uuid4(), _user(uuid.uuid4()), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Farm not found"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_farm_history_denies_non_owner_farmer():
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_result(_farm(farm_id, uuid.uuid4())))

    with pytest.raises(HTTPException) as exc_info:
        await get_farm_history(farm_id, _user(uuid.uuid4()), db)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorized for this farm"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_can_read_any_farm_history():
    farm_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_result(_farm(farm_id, uuid.uuid4())),
        _collection_result([]),
        _collection_result([]),
        _collection_result([]),
    ])

    response = await get_farm_history(
        farm_id,
        _user(admin_id, role=RoleEnum.admin),
        db,
        limit=100,
        offset=0,
    )

    assert response.farm_id == farm_id
    assert response.readings == []
    assert response.checkins == []
    assert response.predictions == []
    assert len(db.execute.await_args_list) == 4
