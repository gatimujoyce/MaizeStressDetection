import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.models import Farm, SensorReading, User
from app.routers.readings import classify_latest


def _db(farm, reading):
    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = farm
    reading_result = MagicMock()
    reading_result.scalar_one_or_none.return_value = reading
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[farm_result, reading_result])
    return db


def _farm_and_user():
    user = User(id=uuid.uuid4(), name="T", phone="+254700000000", password_hash="h")
    farm = Farm(id=uuid.uuid4(), user_id=user.id, name="F", location="L", soil_type="loam")
    return farm, user


def _reading(farm, temperature=38.0):
    return SensorReading(id=uuid.uuid4(), farm_id=farm.id, soil_moisture=24.0, temperature=temperature,
                         humidity=35.0, leaf_wetness=14.0, recorded_at=datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_classification_is_503_when_real_models_are_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "ML_ROOT", "")
    monkeypatch.setattr("app.services.real_inference._runtime", None)
    farm, user = _farm_and_user()
    with pytest.raises(HTTPException) as exc:
        await classify_latest(farm.id, user, _db(farm, _reading(farm)))
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_classification_is_404_without_readings():
    farm, user = _farm_and_user()
    with pytest.raises(HTTPException) as exc:
        await classify_latest(farm.id, user, _db(farm, None))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_classification_returns_the_models_label(monkeypatch):
    async def fake(reading, soil_type):
        assert soil_type == "loam" and reading["temperature"] == 38.0
        return {"label": "heat_stress", "title": "Heat Stress", "confidence": 0.97, "model_version": "sensor-v2+x"}

    monkeypatch.setattr("app.services.real_inference.classify_latest_reading", fake)
    farm, user = _farm_and_user()
    reading = _reading(farm)
    result = await classify_latest(farm.id, user, _db(farm, reading))
    assert result["label"] == "heat_stress" and result["reading_id"] == reading.id