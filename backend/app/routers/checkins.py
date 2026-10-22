import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db, require_farmer
from app.models import Alert, ChannelEnum, Checkin, Farm, Prediction, SensorReading, User
from app.schemas.predictions import PredictionResponse
from app.services.fusion import compute_severity
from app.services.inference import (
    CheckinInference,
    ImageInput,
    InferenceUnavailableError,
    SensorInput,
    get_checkin_inference_pipeline,
)
from app.services.recommend import get_recommendation
from app.services.sms import send_sms

router = APIRouter(prefix="/farms/{farm_id}/checkins", tags=["checkins"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger = logging.getLogger(__name__)


def validate_and_read_image(image: UploadFile) -> bytes:
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    image.file.seek(0, os.SEEK_END)
    size = image.file.tell()
    image.file.seek(0)
    if size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    return image.file.read()


def build_prediction_data(
    checkin_id: uuid.UUID,
    inference: CheckinInference,
) -> dict:
    severity = compute_severity(
        disease_label=inference.disease.label,
        disease_conf=inference.disease.confidence,
        sensor_label=inference.sensor.label,
        sensor_conf=inference.sensor.confidence,
        leaf_wetness_proxy=inference.leaf_wetness_proxy,
        triage_result=inference.triage.label,
    )
    return {
        "id": uuid.uuid4(),
        "checkin_id": checkin_id,
        "reading_id": None,
        "triage_result": inference.triage.label,
        "disease_label": inference.disease.label,
        "disease_conf": inference.disease.confidence,
        "sensor_label": inference.sensor.label,
        "sensor_conf": inference.sensor.confidence,
        "nutrient_label": inference.nutrient.label,
        "nutrient_conf": inference.nutrient.confidence,
        "severity": severity,
        "recommendation": get_recommendation(inference.disease.label, severity),
        "model_versions": inference.model_versions,
        "created_at": datetime.now(timezone.utc),
    }


async def check_farm_access(
    farm_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Farm:
    result = await db.execute(
        select(Farm).where(
            Farm.id == farm_id,
            Farm.user_id == user_id,
            Farm.deleted_at.is_(None),
        )
    )
    farm = result.scalar_one_or_none()
    if farm is None:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.post("", response_model=PredictionResponse)
async def checkin_and_predict(
    farm_id: uuid.UUID,
    image: UploadFile = File(...),
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db),
):
    farm = await check_farm_access(farm_id, current_user.id, db)
    image_content = validate_and_read_image(image)

    try:
        inference_pipeline = get_checkin_inference_pipeline()
    except InferenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sensor_result = await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id)
        .order_by(desc(SensorReading.recorded_at))
        .limit(1)
    )
    latest_reading = sensor_result.scalar_one_or_none()
    sensor_input = (
        SensorInput(
            soil_moisture=latest_reading.soil_moisture,
            temperature=latest_reading.temperature,
            humidity=latest_reading.humidity,
            leaf_wetness=latest_reading.leaf_wetness,
        )
        if latest_reading
        else None
    )

    try:
        inference = await inference_pipeline.predict(
            ImageInput(content=image_content, content_type=image.content_type or ""),
            sensor_input,
        )
    except InferenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    checkin_id = uuid.uuid4()
    extension = "jpg" if image.content_type == "image/jpeg" else "png"
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{extension}")
    with open(filepath, "wb") as buffer:
        buffer.write(image_content)

    new_checkin = Checkin(
        id=checkin_id,
        farm_id=farm_id,
        image_path=filepath,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_checkin)

    prediction_data = build_prediction_data(checkin_id, inference)
    prediction_data["reading_id"] = latest_reading.id if latest_reading else None
    new_prediction = Prediction(**prediction_data)
    db.add(new_prediction)

    if new_prediction.severity in ("Medium", "High"):
        new_alert = Alert(
            id=uuid.uuid4(),
            prediction_id=new_prediction.id,
            farm_id=farm_id,
            severity=new_prediction.severity,
            channel=(
                ChannelEnum.sms
                if new_prediction.severity == "High"
                else ChannelEnum.app
            ),
            status="pending",
            sent_at=None,
        )
        db.add(new_alert)

        if new_prediction.severity == "High":
            message = (
                f"MaizeStress Alert: {new_prediction.severity} severity for "
                f"{new_prediction.disease_label} on {farm.name[:20]}. "
                f"{new_prediction.recommendation}"
            )
            try:
                sms_sent = await asyncio.wait_for(
                    asyncio.to_thread(send_sms, current_user.phone, message),
                    timeout=10.0,
                )
            except Exception:
                logger.exception("Failed to send check-in alert SMS")
                sms_sent = False

            if sms_sent:
                new_alert.status = "sent"
                new_alert.sent_at = datetime.now(timezone.utc)
            else:
                new_alert.status = "failed"

    await db.commit()
    await db.refresh(new_prediction)
    return new_prediction
