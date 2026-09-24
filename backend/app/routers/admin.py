from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import uuid

from app.core.deps import get_db, require_admin
from app.models import User, Farm, Feedback, ModelVersion, RetrainingJob, Alert
from app.schemas.auth import UserResponse
from app.schemas.farms import FarmResponse
from app.schemas.predictions import FeedbackResponse
from app.schemas.admin import ModelVersionResponse, ModelVersionUpdate, RetrainingJobResponse, RetrainRequest

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[UserResponse])
async def admin_users(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User))
    return res.scalars().all()

@router.get("/farms", response_model=List[FarmResponse])
async def admin_farms(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Farm))
    return res.scalars().all()

@router.get("/feedback", response_model=List[FeedbackResponse])
async def admin_feedback(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Feedback))
    return res.scalars().all()

@router.get("/model-versions", response_model=List[ModelVersionResponse])
async def get_model_versions(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelVersion))
    return res.scalars().all()

@router.patch("/model-versions/{id}", response_model=ModelVersionResponse)
async def update_model_version(id: uuid.UUID, update_data: ModelVersionUpdate, current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ModelVersion).where(ModelVersion.id == id))
    mv = res.scalar_one_or_none()
    if not mv: raise HTTPException(404, "Not found")
    mv.is_active = update_data.is_active
    await db.commit()
    await db.refresh(mv)
    return mv

@router.get("/retraining-jobs", response_model=List[RetrainingJobResponse])
async def get_retraining_jobs(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RetrainingJob))
    return res.scalars().all()

@router.post("/retrain")
async def trigger_retrain(req: RetrainRequest, current_admin: User = Depends(require_admin)):
    return {"status": "started", "job_id": str(uuid.uuid4()), "model_name": req.model_name}

@router.get("/sms-log")
async def get_sms_log(current_admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Alert).where(Alert.channel == 'sms'))
    # Return as generic dictionaries since there's no specific SMS response schema requested
    # We can just return exactly Alert schema matches
    return res.scalars().all()
