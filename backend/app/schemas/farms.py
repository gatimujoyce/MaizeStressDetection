from pydantic import BaseModel
from typing import Optional
from app.models import SoilTypeEnum
import uuid

class FarmCreate(BaseModel):
    name: str
    location: str
    soil_type: SoilTypeEnum

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    soil_type: Optional[SoilTypeEnum] = None

class FarmResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    location: str
    soil_type: SoilTypeEnum

    model_config = {"from_attributes": True}
