import io
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.deps import get_db, require_farmer
from app.main import app
from app.models import Farm, SensorReading, User
from app.routers import checkins
from app.services.inference import ImageInput, SensorInput, StubCheckinInferencePipeline


EXPECTED = {
    "healthy": ("Low", "Healthy", "Normal", "in_scope", "No Deficiency"),
    "common_rust": (
        "High",
        "Common Rust",
        "Waterlogging Risk",
        "in_scope",
        "No Deficiency",
    ),
    "northern_leaf_blight": (
        "High",
        "Northern Leaf Blight",
        "Waterlogging Risk",
        "in_scope",
        "No Deficiency",
    ),
    "gray_leaf_spot": (
        "High",
        "Gray Leaf Spot",
        "Heat Stress",
        "in_scope",
        "No Deficiency",
    ),
    "drought_stress": (
        "Medium",
        "Healthy",
        "Drought Stress",
        "in_scope",
        "No Deficiency",
    ),
    "heat_stress": (
        "Medium",
        "Healthy",
        "Heat Stress",
        "in_scope",
        "No Deficiency",
    ),
    "waterlogging_risk": (
        "Medium",
        "Healthy",
        "Waterlogging Risk",
        "in_scope",
        "No Deficiency",
    ),
    "nutrient_deficiency": (
        "Low",
        "Healthy",
        "Normal",
        "in_scope",
        "Nitrogen Deficiency",
    ),
    "out_of_scope": (
        "Inconclusive",
        "Healthy",
        "Normal",
        "out_of_scope",
        "No Deficiency",
    ),
    "inconclusive": (
        "Inconclusive",
        "Common Rust",
        "Normal",
        "in_scope",
        "No Deficiency",
    ),
}


def _make_db(reading=None):
    farm_id = uuid.uuid4()
    user_id = uuid.uuid4()
    if reading is not None:
        reading.farm_id = farm_id
    farm = Farm(
        id=farm_id,
        user_id=user_id,
        name="Stub Test Farm",
        location="Test",
        soil_type="loam",
    )
    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = farm
    reading_result = MagicMock()
    reading_result.scalar_one_or_none.return_value = reading

    db = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock(side_effect=[farm_result, reading_result])
    user = User(
        id=user_id,
        name="Stub Test User",
        phone="+254700000000",
        password_hash="not-used",
    )
    return db, farm_id, user


def _post_checkin(client, farm_id):
    return client.post(
        f"/farms/{farm_id}/checkins",
        files={"image": ("leaf.jpg", io.BytesIO(b"image bytes"), "image/jpeg")},
    )


@pytest.fixture
def backend_client(monkeypatch, tmp_path):
    db, farm_id, user = _make_db()
    monkeypatch.setattr(settings, "CHECKIN_INFERENCE_MODE", "demo")
    monkeypatch.setattr(checkins, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(checkins, "send_sms", lambda *_args: False)

    async def override_user():
        return user

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_farmer] = override_user
    try:
        with TestClient(app) as client:
            yield client, farm_id, db
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.mark.parametrize("scenario", ("random", *EXPECTED.keys()))
def test_checkin_endpoint_runs_each_stub_scenario(
    scenario, backend_client, monkeypatch
):
    client, farm_id, db = backend_client
    monkeypatch.setenv("STUB_SCENARIO", scenario)

    response = _post_checkin(client, farm_id)

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["model_versions"]["inference_mode"] == "stub"
    if scenario == "random":
        assert result["severity"] in {value[0] for value in EXPECTED.values()}
        assert result["disease_label"] in {
            value[1] for value in EXPECTED.values()
        }
        assert result["sensor_label"] in {
            value[2] for value in EXPECTED.values()
        }
        return

    expected_severity, disease, sensor, triage, nutrient = EXPECTED[scenario]
    assert result["severity"] == expected_severity
    assert result["disease_label"] == disease
    assert result["sensor_label"] == sensor
    assert result["triage_result"] == triage
    assert result["nutrient_label"] == nutrient
    assert db.commit.await_count == 1


def test_checkin_endpoint_prefers_latest_farm_sensor_reading(
    monkeypatch, tmp_path
):
    reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=uuid.uuid4(),
        soil_moisture=30.0,
        temperature=24.0,
        humidity=55.0,
        leaf_wetness=4.0,
    )
    db, farm_id, user = _make_db(reading)
    monkeypatch.setenv("STUB_SCENARIO", "drought_stress")
    monkeypatch.setattr(settings, "CHECKIN_INFERENCE_MODE", "demo")
    monkeypatch.setattr(checkins, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(checkins, "send_sms", lambda *_args: False)

    async def override_user():
        return user

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_farmer] = override_user
    try:
        with TestClient(app) as client:
            response = _post_checkin(client, farm_id)
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)

    assert response.status_code == 200, response.text
    assert response.json()["sensor_label"] == "Waterlogging Risk"


def test_app_starts_and_checkin_works_without_model_artifacts(
    backend_client, monkeypatch
):
    client, farm_id, _db = backend_client
    expected = EXPECTED["healthy"]
    monkeypatch.setattr(settings, "CHECKIN_INFERENCE_MODE", "real")
    monkeypatch.setenv("STUB_SCENARIO", "healthy")
    response = _post_checkin(client, farm_id)

    assert client.get("/").status_code == 200
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["severity"] == expected[0]
    assert result["disease_label"] == expected[1]
    assert result["model_versions"] == {
        "inference_mode": "stub",
        "triage": "stub",
        "disease": "stub",
        "sensor": "stub",
        "nutrient": "stub",
    }


@pytest.mark.asyncio
async def test_random_scenario_changes_between_consecutive_selections(monkeypatch):
    monkeypatch.setenv("STUB_SCENARIO", "random")
    monkeypatch.setattr("app.services.inference._last_random_scenario", None)
    monkeypatch.setattr(
        "app.services.inference.random.choice",
        lambda choices: choices[0],
    )
    pipeline = StubCheckinInferencePipeline()
    image = ImageInput(b"image", "image/jpeg")
    reading = SensorInput(30.0, 24.0, 55.0, 4.0)

    first = await pipeline.predict(image, reading)
    second = await pipeline.predict(image, reading)

    assert first.disease.label != second.disease.label
