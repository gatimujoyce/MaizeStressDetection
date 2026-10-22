from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from app.core.deps import get_db, require_farmer
from app.models import Alert, User, Farm, RoleEnum
from app.schemas.alerts import AlertResponse

router = APIRouter(prefix="/farms/{farm_id}/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    # Verify farm ownership
    result_farm = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == current_user.id, Farm.deleted_at.is_(None)))
    if not result_farm.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Farm not found")
        
    result = await db.execute(select(Alert).where(Alert.farm_id == farm_id))
    return result.scalars().all()

@router.patch("/{alert_id}", response_model=AlertResponse)
async def acknowledge_alert(
    farm_id: uuid.UUID,
    alert_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    farm_result = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = farm_result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.user_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")

    alert_result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.farm_id == farm_id)
    )
    alert = alert_result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status != "acknowledged":
        alert.status = "acknowledged"
        await db.commit()
        await db.refresh(alert)

    return alert
