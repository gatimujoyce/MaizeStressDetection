from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from app.core.deps import get_db, require_farmer
from app.models import Alert, User, Farm
from app.schemas.alerts import AlertResponse

router = APIRouter(prefix="/farms/{farm_id}/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    # Verify farm ownership
    result_farm = await db.execute(select(Farm).where(Farm.id == farm_id, Farm.user_id == current_user.id))
    if not result_farm.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await db.execute(select(Alert).where(Alert.farm_id == farm_id))
    return result.scalars().all()
