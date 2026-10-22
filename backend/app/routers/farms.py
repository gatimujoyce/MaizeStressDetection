from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
import uuid
from typing import List
from datetime import datetime, timezone

from app.core.deps import get_db, require_farmer
from app.models import Farm, User, RoleEnum, Checkin, Prediction, SensorReading
from app.schemas.farms import (
    FarmCreate,
    FarmUpdate,
    FarmResponse,
    FarmStatusResponse,
    FarmHistoryResponse,
)

router = APIRouter(prefix="/farms", tags=["farms"])

@router.post("", response_model=FarmResponse)
async def create_farm(
    farm_in: FarmCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    new_farm = Farm(id=uuid.uuid4(), user_id=current_user.id, **farm_in.model_dump())
    db.add(new_farm)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Farm name already exists for this user")
    await db.refresh(new_farm)
    return new_farm

@router.get("", response_model=List[FarmResponse])
async def read_farms(
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.user_id == current_user.id, Farm.deleted_at.is_(None)))
    return result.scalars().all()

@router.get("/{farm_id}/status", response_model=FarmStatusResponse)
async def get_farm_status(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    farm_result = await db.execute(
        select(Farm).where(Farm.id == farm_id, Farm.deleted_at.is_(None))
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.user_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

    prediction_result = await db.execute(
        select(Prediction)
        .join(Checkin)
        .where(Checkin.farm_id == farm_id)
        .order_by(desc(Prediction.created_at))
        .limit(1)
    )
    latest_prediction = prediction_result.scalar_one_or_none()

    return FarmStatusResponse(
        farm_id=farm_id,
        status=(latest_prediction.severity or "unknown") if latest_prediction else "unknown",
        latest_prediction=latest_prediction,
    )

@router.get("/{farm_id}/history", response_model=FarmHistoryResponse)
async def get_farm_history(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    farm_result = await db.execute(
        select(Farm).where(Farm.id == farm_id, Farm.deleted_at.is_(None))
    )
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.user_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

    readings_result = await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id)
        .order_by(desc(SensorReading.recorded_at), desc(SensorReading.id))
        .limit(limit)
        .offset(offset)
    )
    checkins_result = await db.execute(
        select(Checkin)
        .where(Checkin.farm_id == farm_id)
        .order_by(desc(Checkin.created_at), desc(Checkin.id))
        .limit(limit)
        .offset(offset)
    )
    predictions_result = await db.execute(
        select(Prediction)
        .join(Checkin)
        .where(Checkin.farm_id == farm_id)
        .order_by(desc(Prediction.created_at), desc(Prediction.id))
        .limit(limit)
        .offset(offset)
    )

    return FarmHistoryResponse(
        farm_id=farm_id,
        readings=readings_result.scalars().all(),
        checkins=checkins_result.scalars().all(),
        predictions=predictions_result.scalars().all(),
    )

@router.patch("/{id}", response_model=FarmResponse)
async def update_farm(
    id: uuid.UUID,
    farm_in: FarmUpdate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == id, Farm.user_id == current_user.id, Farm.deleted_at.is_(None)))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    update_data = farm_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(farm, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Farm name already exists for this user")
    await db.refresh(farm)
    return farm

@router.get("/{id}", response_model=FarmResponse)
async def read_farm(
    id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == id, Farm.user_id == current_user.id, Farm.deleted_at.is_(None)))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

@router.delete("/{id}", response_model=dict)
async def delete_farm(
    id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == id, Farm.user_id == current_user.id, Farm.deleted_at.is_(None)))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farm.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "success", "message": "Farm deleted"}
