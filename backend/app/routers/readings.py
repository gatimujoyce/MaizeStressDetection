from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, or_
import uuid
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.deps import get_db, require_farmer
from app.models import Alert, SensorReading, Farm, SourceEnum, User
from app.schemas.readings import SensorReadingCreate, SensorReadingResponse
from app.services.nutrient_rules import LEVELS_BY_FIELD, NPK_FIELDS

router = APIRouter(prefix="/farms/{farm_id}/readings", tags=["readings"])

async def check_farm_access(farm_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == user_id, Farm.deleted_at.is_(None)))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

@router.post("", response_model=SensorReadingResponse)
async def create_reading(
    farm_id: uuid.UUID,
    reading_in: SensorReadingCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    farm = await check_farm_access(farm_id, current_user.id, db)
    return await store_reading(db, farm, reading_in, SourceEnum.simulated)


async def store_reading(db: AsyncSession, farm: Farm, reading_in: SensorReadingCreate, source):
    """Check and save one reading for a plot, then run the alert checks. Used by the dashboard and by sensor boxes."""
    farm_id = farm.id
    data = reading_in.model_dump()
    if not farm.has_npk_sensor and any(data.get(f) is not None for f in NPK_FIELDS):
        raise HTTPException(
            status_code=422,
            detail="This plot is not set up with an NPK sensor. Turn on the NPK sensor setting for the plot first.")
    recorded_at = data.pop("recorded_at", None)
    now = datetime.now(timezone.utc)
    if recorded_at is None:
        recorded_at = now
    else:
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)
        if recorded_at > now + timedelta(minutes=5):
            raise HTTPException(status_code=422, detail="recorded_at cannot be in the future")
    new_reading = SensorReading(
        id=uuid.uuid4(),
        farm_id=farm_id,
        recorded_at=recorded_at,
        source=source,
        **data,
    )
    db.add(new_reading)
    await db.commit()
    await db.refresh(new_reading)
    from app.services.sensor_alerts import evaluate_reading
    await evaluate_reading(db, new_reading)
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

@router.get("/trend")
async def reading_trend(
    farm_id: uuid.UUID,
    span: str = Query("7d", alias="range", pattern="^(24h|7d|30d)$"),
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    """Readings grouped into time buckets for the Trends page, with the day-on-day change and the sensor alerts that were
    open in the period. range is 24h, 7d or 30d."""
    from app.services.trends import DAY, FIELDS, RANGES, build_trend
    farm = await check_farm_access(farm_id, current_user.id, db)
    now = datetime.now(timezone.utc)
    window, _ = RANGES[span]
    fetch_start = now - max(window, 2 * DAY)  # two days are needed for the day-on-day change
    rows = (await db.execute(
        select(SensorReading)
        .where(SensorReading.farm_id == farm_id,
               SensorReading.recorded_at >= fetch_start,
               SensorReading.recorded_at <= now + timedelta(minutes=5))
        .order_by(SensorReading.recorded_at)
    )).scalars().all()
    fields = FIELDS + NPK_FIELDS if farm.has_npk_sensor else FIELDS
    readings = [{"recorded_at": r.recorded_at, **{f: getattr(r, f) for f in fields}} for r in rows]
    alert_rows = (await db.execute(
        select(Alert).where(Alert.farm_id == farm_id, Alert.source == "sensor", Alert.created_at <= now,
                            or_(Alert.resolved_at.is_(None), Alert.resolved_at >= now - window))
    )).scalars().all()
    alerts = [{"id": a.id, "stress_class": a.stress_class, "severity": a.severity,
               "created_at": a.created_at, "resolved_at": a.resolved_at} for a in alert_rows]
    from app.services.sensor_status import label_readings
    labels = await label_readings(readings, getattr(farm.soil_type, "value", farm.soil_type))
    return build_trend(readings, alerts, span, now, labels, fields=fields,
                       nutrient_levels=LEVELS_BY_FIELD if farm.has_npk_sensor else None)


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


@router.get("/latest/classification")
async def classify_latest(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    """What the real sensor model says about the farm's latest reading. 503 when the real models are not configured."""
    from app.services.inference import InferenceUnavailableError
    from app.services.real_inference import classify_latest_reading
    farm = await check_farm_access(farm_id, current_user.id, db)
    result = await db.execute(select(SensorReading).where(SensorReading.farm_id == farm_id).order_by(desc(SensorReading.recorded_at)).limit(1))
    reading = result.scalar_one_or_none()
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")
    try:
        label = await classify_latest_reading(
            {"soil_moisture": reading.soil_moisture, "temperature": reading.temperature,
             "humidity": reading.humidity, "leaf_wetness": reading.leaf_wetness},
            getattr(farm.soil_type, "value", farm.soil_type))
    except InferenceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"reading_id": reading.id, "recorded_at": reading.recorded_at, **label}