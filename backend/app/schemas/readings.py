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
    nitrogen_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)     # NPK sensor values, mg/kg
    phosphorus_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)
    potassium_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)
    recorded_at: Optional[datetime] = None

class SensorReadingResponse(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    leaf_wetness: float
    nitrogen_mg_kg: Optional[float] = None
    phosphorus_mg_kg: Optional[float] = None
    potassium_mg_kg: Optional[float] = None
    id: uuid.UUID
    farm_id: uuid.UUID
    recorded_at: datetime
    source: SourceEnum

    model_config = {"from_attributes": True}
