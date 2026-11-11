"""Endpoints for a plot's sensor box. It logs in with a device key (header X-Device-Key), not a farmer's password."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models import DeviceKey, Farm, SourceEnum
from app.routers.readings import store_reading
from app.schemas.readings import SensorReadingCreate, SensorReadingResponse
from app.services.device_keys import hash_key

router = APIRouter(prefix="/device", tags=["device"])


async def device_context(x_device_key: Optional[str] = Header(default=None), db: AsyncSession = Depends(get_db)):
    """The farm and key behind a device key. Fails with 401 for a missing, unknown or revoked key."""
    if not x_device_key:
        raise HTTPException(status_code=401, detail="Missing device key")
    row = (await db.execute(select(DeviceKey).where(DeviceKey.key_hash == hash_key(x_device_key.strip())))).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid or revoked device key")
    farm = (await db.execute(select(Farm).where(Farm.id == row.farm_id, Farm.deleted_at.is_(None)))).scalar_one_or_none()
    if farm is None:
        raise HTTPException(status_code=403, detail="This plot is no longer active")
    return row, farm


@router.get("/whoami")
async def whoami(ctx=Depends(device_context)):
    """Lets an installer check a key: which plot it belongs to and whether the plot takes NPK values."""
    _, farm = ctx
    return {"farm_name": farm.name, "has_npk_sensor": farm.has_npk_sensor, "server_time": datetime.now(timezone.utc)}


@router.post("/readings", response_model=SensorReadingResponse)
async def post_device_reading(reading_in: SensorReadingCreate, ctx=Depends(device_context), db: AsyncSession = Depends(get_db)):
    """A sensor box posts one reading for its own plot. Handled exactly like a reading from the dashboard, then marked as real."""
    key, farm = ctx
    key.last_used_at = datetime.now(timezone.utc)
    return await store_reading(db, farm, reading_in, SourceEnum.real)
