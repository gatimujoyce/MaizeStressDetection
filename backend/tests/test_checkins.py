import asyncio
import io
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.models import Alert, Farm, SensorReading, User
from app.routers.checkins import checkin_and_predict
from app.services.fusion import compute_severity
from app.services.inference import DemoCheckinInferencePipeline


@pytest.mark.parametrize(
    ("disease", "disease_conf", "sensor", "sensor_conf", "wetness", "triage", "expected"),
    [
        ("Common Rust", 0.5, "Normal", 0.8, 2.0, "in_scope", "Inconclusive"),
        ("Common Rust", 0.9, "Normal", 0.8, 2.0, "out_of_scope", "Inconclusive"),
        ("Healthy", 0.9, "Normal", 0.8, 2.0, "in_scope", "Low"),
        ("Healthy", 0.9, "Drought Stress", 0.8, 2.0, "in_scope", "Medium"),
        ("Common Rust", 0.9, "Waterlogging Risk", 0.8, 4.0, "in_scope", "High"),
        ("Northern Leaf Blight", 0.9, "Normal", 0.8, 2.0, "in_scope", "High"),
        ("Northern Leaf Blight", 0.9, "Normal", 0.8, 4.0, "in_scope", "Medium"),
        ("Gray Leaf Spot", 0.9, "Heat Stress", 0.8, 2.0, "in_scope", "High"),
        ("Gray Leaf Spot", 0.9, "Normal", 0.8, 3.0, "in_scope", "Medium"),
    ],
)
def test_compute_severity_matrix(
    disease, disease_conf, sensor, sensor_conf, wetness, triage, expected
):
    assert compute_severity(
        disease, disease_conf, sensor, sensor_conf, wetness, triage
    ) == expected


def _create_mock_checkin_context(image_bytes=b"fake image bytes"):
    db = AsyncMock()
    db.add = MagicMock()

    user = User(
        id=uuid.uuid4(),
        name="Test User",
        phone="+254700000000",
        password_hash="hash",
    )
    farm_id = uuid.uuid4()
    farm = Farm(
        id=farm_id,
        user_id=user.id,
        name="Test Farm",
        location="Loc",
        soil_type="loam",
    )
    reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=farm_id,
        soil_moisture=30.0,
        temperature=24.0,
        humidity=55.0,
        leaf_wetness=2.0,
    )

    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = farm
    sensor_result = MagicMock()
    sensor_result.scalar_one_or_none.return_value = reading
    db.execute = AsyncMock(side_effect=[farm_result, sensor_result])

    image = MagicMock(spec=UploadFile)
    image.file = io.BytesIO(image_bytes)
    image.content_type = "image/jpeg"
    image.filename = "test.jpeg"
    return db, image, user, farm_id


def _added_alerts(db):
    return [
        obj
        for call in db.add.call_args_list
        for obj in call.args
        if isinstance(obj, Alert)
    ]


@pytest.mark.asyncio
async def test_checkin_rejects_farm_not_owned_by_user():
    db, image, user, farm_id = _create_mock_checkin_context()
    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=farm_result)

    with pytest.raises(HTTPException) as exc_info:
        await checkin_and_predict(farm_id, image, user, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Farm not found"
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_checkin_persists_prediction_and_marks_successful_sms():
    db, image, user, farm_id = _create_mock_checkin_context()

    with patch(
        "app.routers.checkins.get_checkin_inference_pipeline",
        return_value=DemoCheckinInferencePipeline(),
    ), patch("app.routers.checkins.os.path.join", return_value="uploads/test.jpg"), patch(
        "app.routers.checkins.open"
    ), patch("app.routers.checkins.send_sms", return_value=True) as send_sms:
        prediction = await checkin_and_predict(farm_id, image, user, db)

    assert prediction.severity == "High"
    assert prediction.recommendation
    assert prediction.model_versions["inference_mode"] == "demo"
    send_sms.assert_called_once()
    assert send_sms.call_args.args[0] == user.phone
    assert "Test Farm" in send_sms.call_args.args[1]
    assert len(_added_alerts(db)) == 1
    assert _added_alerts(db)[0].status == "sent"
    assert _added_alerts(db)[0].sent_at is not None
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(prediction)


@pytest.mark.asyncio
async def test_checkin_marks_failed_sms_without_losing_prediction():
    db, image, user, farm_id = _create_mock_checkin_context()

    with patch(
        "app.routers.checkins.get_checkin_inference_pipeline",
        return_value=DemoCheckinInferencePipeline(),
    ), patch("app.routers.checkins.os.path.join", return_value="uploads/test.jpg"), patch(
        "app.routers.checkins.open"
    ), patch("app.routers.checkins.send_sms", return_value=False):
        prediction = await checkin_and_predict(farm_id, image, user, db)

    assert prediction.severity == "High"
    assert _added_alerts(db)[0].status == "failed"
    assert _added_alerts(db)[0].sent_at is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_checkin_marks_sms_exception_as_failed_and_keeps_prediction():
    db, image, user, farm_id = _create_mock_checkin_context()

    with patch(
        "app.routers.checkins.get_checkin_inference_pipeline",
        return_value=DemoCheckinInferencePipeline(),
    ), patch("app.routers.checkins.os.path.join", return_value="uploads/test.jpg"), patch(
        "app.routers.checkins.open"
    ), patch(
        "app.routers.checkins.send_sms",
        side_effect=RuntimeError("SMS gateway unavailable"),
    ):
        prediction = await checkin_and_predict(farm_id, image, user, db)

    assert prediction.severity == "High"
    assert _added_alerts(db)[0].status == "failed"
    assert _added_alerts(db)[0].sent_at is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_checkin_marks_timed_out_sms_as_failed():
    db, image, user, farm_id = _create_mock_checkin_context()

    def slow_send_sms(*_args, **_kwargs):
        time.sleep(0.05)
        return True

    wait_for = asyncio.wait_for

    async def short_wait_for(awaitable, timeout=None):
        del timeout
        return await wait_for(awaitable, timeout=0.001)

    with patch(
        "app.routers.checkins.get_checkin_inference_pipeline",
        return_value=DemoCheckinInferencePipeline(),
    ), patch("app.routers.checkins.os.path.join", return_value="uploads/test.jpg"), patch(
        "app.routers.checkins.open"
    ), patch(
        "app.routers.checkins.send_sms", side_effect=slow_send_sms
    ), patch("app.routers.checkins.asyncio.wait_for", side_effect=short_wait_for):
        prediction = await checkin_and_predict(farm_id, image, user, db)

    assert prediction.severity == "High"
    assert _added_alerts(db)[0].status == "failed"
    assert _added_alerts(db)[0].sent_at is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content_type", "image_bytes"),
    [
        ("text/plain", b"not an image"),
        ("image/jpeg", b"x" * (5 * 1024 * 1024 + 1)),
    ],
    ids=["unsupported_media_type", "image_over_5mb"],
)
async def test_checkin_rejects_invalid_or_oversized_image(content_type, image_bytes):
    db, image, user, farm_id = _create_mock_checkin_context(image_bytes)
    image.content_type = content_type

    with pytest.raises(HTTPException) as exc_info:
        await checkin_and_predict(farm_id, image, user, db)

    assert exc_info.value.status_code == 400
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
