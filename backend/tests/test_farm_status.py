import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models import Farm, Prediction, RoleEnum, User
from app.routers.farms import get_farm_status


def _result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.mark.asyncio
async def test_farm_status_returns_latest_prediction():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    prediction = Prediction(
        id=uuid.uuid4(),
        checkin_id=uuid.uuid4(),
        triage_result="in_scope",
        severity="High",
        model_versions={"disease": "v1"},
        created_at=datetime.now(timezone.utc),
    )
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(Farm(id=farm_id, user_id=owner_id, name="Farm", location="Here", soil_type="loam")),
        _result(prediction),
    ])

    response = await get_farm_status(
        farm_id,
        User(id=owner_id, name="Owner", phone="123", password_hash="hash"),
        db,
    )

    assert response.farm_id == farm_id
    assert response.status == "High"
    assert response.latest_prediction.id == prediction.id
    assert response.latest_prediction.created_at == prediction.created_at
    assert response.latest_prediction.disease_label is None


@pytest.mark.asyncio
async def test_farm_status_is_unknown_when_no_prediction_exists():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(Farm(id=farm_id, user_id=owner_id, name="Farm", location="Here", soil_type="loam")),
        _result(None),
    ])

    response = await get_farm_status(
        farm_id,
        User(id=owner_id, name="Owner", phone="123", password_hash="hash"),
        db,
    )

    assert response.farm_id == farm_id
    assert response.status == "unknown"
    assert response.latest_prediction is None


@pytest.mark.asyncio
async def test_farm_status_returns_404_for_missing_farm():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_result(None))

    with pytest.raises(HTTPException) as exc_info:
        await get_farm_status(
            uuid.uuid4(),
            User(id=uuid.uuid4(), name="Owner", phone="123", password_hash="hash"),
            db,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Farm not found"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_farm_status_returns_403_for_non_owner():
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_result(
        Farm(id=farm_id, user_id=uuid.uuid4(), name="Farm", location="Here", soil_type="loam")
    ))

    with pytest.raises(HTTPException) as exc_info:
        await get_farm_status(
            farm_id,
            User(id=uuid.uuid4(), name="Other", phone="456", password_hash="hash"),
            db,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorized for this farm"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_can_read_status_for_any_farm():
    farm_id = uuid.uuid4()
    prediction = Prediction(
        id=uuid.uuid4(),
        checkin_id=uuid.uuid4(),
        triage_result="in_scope",
        severity="Medium",
        model_versions={"disease": "v1"},
        created_at=datetime.now(timezone.utc),
    )
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(Farm(id=farm_id, user_id=uuid.uuid4(), name="Farm", location="Here", soil_type="loam")),
        _result(prediction),
    ])

    response = await get_farm_status(
        farm_id,
        User(
            id=uuid.uuid4(),
            name="Admin",
            phone="789",
            password_hash="hash",
            role=RoleEnum.admin,
        ),
        db,
    )

    assert response.status == "Medium"
    assert response.latest_prediction.id == prediction.id
