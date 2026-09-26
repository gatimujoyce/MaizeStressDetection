from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import uuid
from typing import List
from datetime import datetime, timezone

from app.core.deps import get_db, require_farmer
from app.models import SensorReading, Farm, User
from app.schemas.readings import SensorReadingCreate, SensorReadingResponse

router = APIRouter(prefix="/farms/{farm_id}/readings", tags=["readings"])

async def check_farm_access(farm_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

@router.post("", response_model=SensorReadingResponse)
async def create_reading(
    farm_id: uuid.UUID,
    reading_in: SensorReadingCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await check_farm_access(farm_id, current_user.id, db)
    new_reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=farm_id,
        recorded_at=datetime.now(timezone.utc),
        **reading_in.model_dump()
    )
    db.add(new_reading)
    await db.commit()
    await db.refresh(new_reading)
    return new_reading

@router.get("/latest", response_model=SensorReadingResponse)
async def get_latest_reading(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    await check_farm_access(farm_id, current_user.id, db)
    result = await db.execute(select(SensorReading).where(SensorReading.farm_id == farm_id).order_by(desc(SensorReading.recorded_at)).limit(1))
    reading = result.scalar_one_or_none()
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    return reading

@router.get("", response_model=List[SensorReadingResponse])
async def filter_readings(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db),
    from_date: datetime = Query(None, alias="from"),
    to_date: datetime = Query(None, alias="to")
):
    await check_farm_access(farm_id, current_user.id, db)
    query = select(SensorReading).where(SensorReading.farm_id == farm_id)
    if from_date:
        query = query.where(SensorReading.recorded_at >= from_date)
    if to_date:
        query = query.where(SensorReading.recorded_at <= to_date)
    
    result = await db.execute(query.order_by(desc(SensorReading.recorded_at)))
    return result.scalars().all()
