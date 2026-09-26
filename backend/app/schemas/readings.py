from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models import SourceEnum
import uuid

class SensorReadingCreate(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    leaf_wetness: float

class SensorReadingResponse(SensorReadingCreate):
    id: uuid.UUID
    farm_id: uuid.UUID
    recorded_at: datetime
    source: SourceEnum

    model_config = {"from_attributes": True}
