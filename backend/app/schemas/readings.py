from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Optional
from app.models import SourceEnum
import uuid

class SensorReadingCreate(BaseModel):
    # Every value is optional so a box with one dead sensor can still report the rest; at least one value is needed.
    soil_moisture: Optional[float] = Field(default=None, ge=0, le=100)   # percent
    temperature: Optional[float] = Field(default=None, ge=-20, le=60)    # degrees Celsius
    humidity: Optional[float] = Field(default=None, ge=0, le=100)        # percent relative humidity
    leaf_wetness: Optional[float] = Field(default=None, ge=0)            # left out: worked out from temperature and humidity
    battery_percent: Optional[float] = Field(default=None, ge=0, le=100)
    firmware: Optional[str] = Field(default=None, max_length=40)
    nitrogen_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)     # NPK sensor values, mg/kg
    phosphorus_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)
    potassium_mg_kg: Optional[float] = Field(default=None, ge=0, le=10000)
    recorded_at: Optional[datetime] = None

    @model_validator(mode="after")
    def at_least_one_value(self):
        measured = (self.soil_moisture, self.temperature, self.humidity, self.leaf_wetness,
                    self.nitrogen_mg_kg, self.phosphorus_mg_kg, self.potassium_mg_kg)
        if all(v is None for v in measured):
            raise ValueError("A reading needs at least one sensor value")
        return self

class SensorReadingResponse(BaseModel):
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    leaf_wetness: Optional[float] = None
    battery_percent: Optional[float] = None
    firmware: Optional[str] = None
    nitrogen_mg_kg: Optional[float] = None
    phosphorus_mg_kg: Optional[float] = None
    potassium_mg_kg: Optional[float] = None
    id: uuid.UUID
    farm_id: uuid.UUID
    recorded_at: datetime
    source: SourceEnum

    model_config = {"from_attributes": True}
