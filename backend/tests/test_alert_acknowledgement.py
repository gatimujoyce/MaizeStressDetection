import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models import Alert, ChannelEnum, Farm, RoleEnum, User
from app.routers.alerts import acknowledge_alert


def _result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _farm(farm_id, owner_id):
    return Farm(
        id=farm_id,
        user_id=owner_id,
        name="Test Farm",
        location="Here",
        soil_type="loam",
    )


def _alert(alert_id, farm_id, status="sent"):
    return Alert(
        id=alert_id,
        prediction_id=uuid.uuid4(),
        farm_id=farm_id,
        severity="High",
        channel=ChannelEnum.sms,
        status=status,
    )


def _user(user_id, role=RoleEnum.farmer):
    return User(
        id=user_id,
        name="Test User",
        phone=str(user_id),
        password_hash="hash",
        role=role,
    )


@pytest.mark.asyncio
async def test_acknowledge_alert_updates_status_and_returns_alert():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    alert = _alert(uuid.uuid4(), farm_id)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(_farm(farm_id, owner_id)),
        _result(alert),
    ])

    response = await acknowledge_alert(farm_id, alert.id, _user(owner_id), db)

    assert response.id == alert.id
    assert response.farm_id == farm_id
    assert response.status == "acknowledged"
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(alert)


@pytest.mark.asyncio
async def test_acknowledge_alert_is_idempotent():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    alert = _alert(uuid.uuid4(), farm_id, status="acknowledged")
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(_farm(farm_id, owner_id)),
        _result(alert),
    ])

    response = await acknowledge_alert(farm_id, alert.id, _user(owner_id), db)

    assert response.status == "acknowledged"
    db.commit.assert_not_awaited()
    db.refresh.assert_not_awaited()


@pytest.mark.asyncio
async def test_acknowledge_alert_returns_404_for_missing_alert():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(_farm(farm_id, owner_id)),
        _result(None),
    ])

    with pytest.raises(HTTPException) as exc_info:
        await acknowledge_alert(farm_id, uuid.uuid4(), _user(owner_id), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Alert not found"


@pytest.mark.asyncio
async def test_acknowledge_alert_returns_404_for_missing_farm():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_result(None))

    with pytest.raises(HTTPException) as exc_info:
        await acknowledge_alert(uuid.uuid4(), uuid.uuid4(), _user(uuid.uuid4()), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Farm not found"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_acknowledge_alert_rejects_alert_from_different_farm():
    owner_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    alert = _alert(uuid.uuid4(), uuid.uuid4())
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(_farm(farm_id, owner_id)),
        _result(None),
    ])

    with pytest.raises(HTTPException) as exc_info:
        await acknowledge_alert(farm_id, alert.id, _user(owner_id), db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Alert not found"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_acknowledge_alert_denies_non_owner():
    farm_id = uuid.uuid4()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_result(_farm(farm_id, uuid.uuid4())))

    with pytest.raises(HTTPException) as exc_info:
        await acknowledge_alert(farm_id, uuid.uuid4(), _user(uuid.uuid4()), db)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Not authorized for this farm"
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_can_acknowledge_alert_for_any_farm():
    farm_id = uuid.uuid4()
    alert = _alert(uuid.uuid4(), farm_id)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _result(_farm(farm_id, uuid.uuid4())),
        _result(alert),
    ])

    response = await acknowledge_alert(
        farm_id,
        alert.id,
        _user(uuid.uuid4(), role=RoleEnum.admin),
        db,
    )

    assert response.status == "acknowledged"
    db.commit.assert_awaited_once()
