import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.models import Farm, User
from app.routers.checkins import build_prediction_data, checkin_and_predict
from app.services.inference import (
    CheckinInference,
    ImageInput,
    InferenceUnavailableError,
    ModelOutput,
    SensorInput,
    DemoCheckinInferencePipeline,
    get_checkin_inference_pipeline,
)


@pytest.mark.asyncio
async def test_demo_pipeline_marks_outputs_as_demo():
    pipeline = DemoCheckinInferencePipeline()
    reading = SensorInput(
        soil_moisture=30.0,
        temperature=24.0,
        humidity=55.0,
        leaf_wetness=4.0,
    )

    result = await pipeline.predict(ImageInput(b"image", "image/jpeg"), reading)

    assert result.triage.label == "Needs attention"
    assert result.disease.label == "Northern Leaf Blight"
    assert result.sensor.label == "Waterlogging Risk"
    assert result.nutrient.label == "Nitrogen Deficiency"
    assert result.leaf_wetness_proxy == 4.0
    assert result.model_versions["inference_mode"] == "demo"
    assert result.model_versions["disease"] == "demo"


def test_real_inference_mode_fails_explicitly_without_models():
    with pytest.raises(InferenceUnavailableError, match="trained model artifacts"):
        get_checkin_inference_pipeline("real")


def test_prediction_stage_keeps_fusion_and_recommendation_separate():
    inference = CheckinInference(
        triage=ModelOutput("in_scope", 0.91),
        disease=ModelOutput("Northern Leaf Blight", 0.94),
        sensor=ModelOutput("Waterlogging Risk", 0.88),
        nutrient=ModelOutput("Nitrogen Deficiency", 0.72),
        leaf_wetness_proxy=4.0,
        model_versions={"inference_mode": "demo"},
    )

    prediction = build_prediction_data(uuid.uuid4(), inference)

    assert prediction["severity"] == "High"
    assert prediction["recommendation"]
    assert prediction["model_versions"] == {"inference_mode": "demo"}


@pytest.mark.asyncio
async def test_checkin_returns_503_in_real_mode_before_storing_upload():
    farm_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    farm_result = MagicMock()
    farm_result.scalar_one_or_none.return_value = Farm(
        id=farm_id,
        user_id=owner_id,
        name="Farm",
        location="Here",
        soil_type="loam",
    )
    db = AsyncMock()
    db.execute = AsyncMock(return_value=farm_result)
    image = MagicMock(spec=UploadFile)
    image.content_type = "image/jpeg"
    image.filename = "leaf.jpg"
    image.file = MagicMock()
    image.file.seek = MagicMock()
    image.file.tell = MagicMock(return_value=10)
    image.file.read = MagicMock(return_value=b"image bytes")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.routers.checkins.get_checkin_inference_pipeline",
            lambda: get_checkin_inference_pipeline("real"),
        )
        with pytest.raises(HTTPException) as exc_info:
            await checkin_and_predict(
                farm_id,
                image,
                User(
                    id=owner_id,
                    name="Owner",
                    phone="123",
                    password_hash="hash",
                ),
                db,
            )

    assert exc_info.value.status_code == 503
    assert "Real check-in inference is not available" in exc_info.value.detail
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
