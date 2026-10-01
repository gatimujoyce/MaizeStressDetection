from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models import SourceEnum
import uuid

class SensorReadingCreate(BaseModel):
    soil_moisture: float = Field(ge=0, le=100)   # percent
    temperature: float = Field(ge=-20, le=60)    # degrees Celsius
    humidity: float = Field(ge=0, le=100)        # percent relative humidity
    leaf_wetness: float = Field(ge=0)

class SensorReadingResponse(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    leaf_wetness: float
    id: uuid.UUID
    farm_id: uuid.UUID
    recorded_at: datetime
    source: SourceEnum

    model_config = {"from_attributes": True}
