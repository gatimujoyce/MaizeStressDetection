from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from app.core.deps import get_db, require_farmer
from app.models import Farm, User
from app.schemas.farms import FarmCreate, FarmUpdate, FarmResponse

router = APIRouter(prefix="/farms", tags=["farms"])

@router.post("", response_model=FarmResponse)
async def create_farm(
    farm_in: FarmCreate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    new_farm = Farm(id=uuid.uuid4(), user_id=current_user.id, **farm_in.model_dump())
    db.add(new_farm)
    await db.commit()
    await db.refresh(new_farm)
    return new_farm

@router.get("", response_model=List[FarmResponse])
async def read_farms(
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.user_id == current_user.id))
    return result.scalars().all()

@router.patch("/{id}", response_model=FarmResponse)
async def update_farm(
    id: uuid.UUID,
    farm_in: FarmUpdate,
    current_user: User = Depends(require_farmer),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Farm).where(Farm.id == id, Farm.user_id == current_user.id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    update_data = farm_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(farm, k, v)
    
    await db.commit()
    await db.refresh(farm)
    return farm
