from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os
import shutil
from datetime import datetime, timezone

from app.core.deps import get_db, require_farmer
from sqlalchemy import desc
from app.models import Farm, User, Checkin, Prediction, SensorReading, Alert, ChannelEnum
from app.schemas.predictions import PredictionResponse
from app.services.fusion import compute_severity
from app.services.recommend import get_recommendation
from app.services.sms import send_sms

router = APIRouter(prefix="/farms/{farm_id}/checkins", tags=["checkins"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def check_farm_access(farm_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

@router.post("", response_model=PredictionResponse)
async def checkin_and_predict(
    farm_id: uuid.UUID,
    image: UploadFile = File(...),
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await check_farm_access(farm_id, current_user.id, db)
    
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    image.file.seek(0, 2)
    size = image.file.tell()
    image.file.seek(0)
    if size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    ext = image.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    checkin_id = uuid.uuid4()
    new_checkin = Checkin(id=checkin_id, farm_id=farm_id, image_path=filepath, created_at=datetime.now(timezone.utc))
    db.add(new_checkin)
    
    # 1. Get farm's latest sensor reading
    sensor_result = await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id)
        .order_by(desc(SensorReading.recorded_at))
        .limit(1)
    )
    latest_reading = sensor_result.scalar_one_or_none()
    
    # 2. Mock triage and disease prediction
    triage_result = "Needs attention"
    disease_label = "Northern Leaf Blight"
    disease_conf = 0.94
    
    # 3. Use sensor reading to mock sensor prediction and leaf wetness proxy
    leaf_wetness_proxy = latest_reading.leaf_wetness if latest_reading else 2.0
    reading_id = latest_reading.id if latest_reading else None
    
    sensor_label = "Waterlogging Risk" if leaf_wetness_proxy > 3 else ("Normal" if leaf_wetness_proxy > 1 else "Heat Stress")
    sensor_conf = 0.88
    
    nutrient_label = "Nitrogen Deficiency"
    nutrient_conf = 0.72
    
    # 4. Compute severity
    severity = compute_severity(
        disease_label=disease_label,
        disease_conf=disease_conf,
        sensor_label=sensor_label,
        sensor_conf=sensor_conf,
        leaf_wetness_proxy=leaf_wetness_proxy,
        triage_result=triage_result
    )

    # 5. Get recommendation
    recommendation = get_recommendation(disease_label, severity)
    
    # 6. Save Prediction
    pred_data = {
        "id": uuid.uuid4(),
        "checkin_id": checkin_id,
        "reading_id": reading_id,
        "triage_result": triage_result,
        "disease_label": disease_label,
        "disease_conf": disease_conf,
        "sensor_label": sensor_label,
        "sensor_conf": sensor_conf,
        "nutrient_label": nutrient_label,
        "nutrient_conf": nutrient_conf,
        "severity": severity,
        "recommendation": recommendation,
        "model_versions": {"triage": "v1.0", "disease": "v2.1", "nutrient": "v1.5"},
        "created_at": datetime.now(timezone.utc)
    }
    new_pred = Prediction(**pred_data)
    db.add(new_pred)
    
    # 7. Create an alert if necessary
    alert_status = "none"
    if severity in ["Medium", "High"]:
        new_alert = Alert(
            id=uuid.uuid4(),
            prediction_id=new_pred.id,
            farm_id=farm_id,
            severity=severity,
            channel=ChannelEnum.sms if severity == "High" else ChannelEnum.app,
            status="pending",
            sent_at=None
        )
        db.add(new_alert)
        
        # 8. Send SMS if High
        if severity == "High":
            msg = f"MaizeStress Alert: {severity} severity for {disease_label}. {recommendation}"
            result = send_sms(current_user.phone, msg)
            if result:
                new_alert.status = "sent"
                new_alert.sent_at = datetime.now(timezone.utc)
                alert_status = "sent"
            else:
                new_alert.status = "failed"
                alert_status = "failed"
    
    await db.commit()
    await db.refresh(new_pred)
    return new_pred
