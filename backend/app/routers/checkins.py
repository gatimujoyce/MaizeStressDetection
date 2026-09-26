from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import os
import shutil
from datetime import datetime, timezone

from app.core.deps import get_db, require_farmer
from app.models import Farm, User, Checkin, Prediction
from app.schemas.predictions import PredictionResponse

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
    
    # Save a faked prediction response object to DB to stub inference models
    pred_data = {
        "id": uuid.uuid4(),
        "checkin_id": checkin_id,
        "reading_id": None,
        "triage_result": "Needs attention",
        "disease_label": "Northern Leaf Blight",
        "disease_conf": 0.94,
        "sensor_label": "Optimal",
        "sensor_conf": 0.88,
        "nutrient_label": "Nitrogen Deficiency",
        "nutrient_conf": 0.72,
        "severity": "Moderate",
        "recommendation": "Apply nitrogen-rich fertilizer immediately.",
        "model_versions": {"triage": "v1.0", "disease": "v2.1", "nutrient": "v1.5"},
        "created_at": datetime.now(timezone.utc)
    }
    new_pred = Prediction(**pred_data)
    db.add(new_pred)
    await db.commit()
    await db.refresh(new_pred)
    return new_pred
