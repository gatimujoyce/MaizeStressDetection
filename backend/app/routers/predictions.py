from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List
from datetime import datetime, timezone

from app.core.deps import get_db, require_farmer
from app.models import Prediction, User, Feedback, Farm, Checkin
from app.schemas.predictions import PredictionResponse, FeedbackCreate, FeedbackResponse

router = APIRouter(tags=["predictions"])

async def check_farm_access(farm_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

@router.get("/farms/{farm_id}/predictions", response_model=List[PredictionResponse])
async def list_predictions(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await check_farm_access(farm_id, current_user.id, db)
    # Join with Checkin to ensure we fetch predictions for this farm
    result = await db.execute(
        select(Prediction).join(Checkin).where(Checkin.farm_id == farm_id)
    )
    return result.scalars().all()

@router.get("/farms/{farm_id}/predictions/{id}", response_model=PredictionResponse)
async def get_prediction(
    farm_id: uuid.UUID,
    id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await check_farm_access(farm_id, current_user.id, db)
    result = await db.execute(
        select(Prediction).join(Checkin).where(Prediction.id == id, Checkin.farm_id == farm_id)
    )
    pred = result.scalar_one_or_none()
    if not pred: raise HTTPException(status_code=404, detail="Prediction not found")
    return pred

@router.post("/predictions/{id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    id: uuid.UUID,
    feedback: FeedbackCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    new_feedback = Feedback(
        id=uuid.uuid4(),
        prediction_id=id,
        created_at=datetime.now(timezone.utc),
        **feedback.model_dump()
    )
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    return new_feedback
