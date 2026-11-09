from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.deps import get_db, require_farmer
from app.models import Alert, Prediction, User, Feedback, Farm, Checkin
from app.schemas.predictions import PredictionResponse, FeedbackCreate, FeedbackResponse, FollowUpCreate, FollowUpDue

router = APIRouter(tags=["predictions"])

async def check_farm_access(farm_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == user_id, Farm.deleted_at.is_(None)))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

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

async def _own_prediction(db, prediction_id, user_id):
    result = await db.execute(
        select(Prediction).join(Checkin).join(Farm)
        .where(Prediction.id == prediction_id, Farm.user_id == user_id, Farm.deleted_at.is_(None))
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


async def _latest_feedback(db, prediction_id):
    result = await db.execute(
        select(Feedback).where(Feedback.prediction_id == prediction_id).order_by(Feedback.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


@router.post("/predictions/{id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    id: uuid.UUID,
    feedback: FeedbackCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    # Prediction must exist and belong to one of the current user's farms
    await _own_prediction(db, id, current_user.id)

    answers = feedback.model_dump()
    row = await _latest_feedback(db, id)
    if row is None:
        row = Feedback(id=uuid.uuid4(), prediction_id=id, created_at=datetime.now(timezone.utc), **answers)
        db.add(row)
    else:
        # Answering again replaces the earlier answers (the follow-up answer is kept).
        for key, value in answers.items():
            setattr(row, key, value)
    # Once the farmer has answered, the photo alert is read and moves to "Earlier".
    await db.execute(update(Alert).where(Alert.prediction_id == id, Alert.status != "acknowledged").values(status="acknowledged"))
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/predictions/{id}/follow-up", response_model=FeedbackResponse)
async def submit_follow_up(
    id: uuid.UUID,
    body: FollowUpCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await _own_prediction(db, id, current_user.id)
    row = await _latest_feedback(db, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Answer the first questions about this result before the follow-up")
    row.follow_up_outcome = body.outcome
    row.follow_up_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return row


@router.get("/farms/{farm_id}/follow-ups", response_model=List[FollowUpDue])
async def list_follow_ups(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    """Results with advice (Medium or High) that the farmer answered FOLLOW_UP_DAYS or more ago and has not followed up."""
    await check_farm_access(farm_id, current_user.id, db)
    now = datetime.now(timezone.utc)
    ready = now - timedelta(days=settings.FOLLOW_UP_DAYS)
    too_old = now - timedelta(days=settings.FOLLOW_UP_DAYS + 21)   # do not nag about very old results
    result = await db.execute(
        select(Feedback, Prediction)
        .join(Prediction, Prediction.id == Feedback.prediction_id)
        .join(Checkin, Checkin.id == Prediction.checkin_id)
        .where(
            Checkin.farm_id == farm_id,
            Prediction.severity.in_(("Medium", "High")),
            Feedback.follow_up_outcome.is_(None),
            Feedback.created_at <= ready,
            Feedback.created_at >= too_old,
        )
        .order_by(Feedback.created_at.desc())
    )
    return [
        FollowUpDue(prediction_id=prediction.id, farm_id=farm_id, label=prediction.disease_label,
                    severity=prediction.severity, advice=prediction.recommendation, answered_at=feedback.created_at)
        for feedback, prediction in result.all()
    ]
