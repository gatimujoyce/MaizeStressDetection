from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models import SoilTypeEnum
from app.schemas.predictions import PredictionResponse
from app.schemas.checkins import CheckinResponse
from app.schemas.readings import SensorReadingResponse
import uuid

class FarmCreate(BaseModel):
    name: str
    location: str
    soil_type: SoilTypeEnum
    size_acres: Optional[float] = Field(default=None, gt=0.0)
    planting_date: Optional[date] = None
    water_source: Optional[str] = None
    seed_variety: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    soil_type: Optional[SoilTypeEnum] = None
    size_acres: Optional[float] = Field(default=None, gt=0.0)
    planting_date: Optional[date] = None
    water_source: Optional[str] = None
    seed_variety: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

class FarmResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    location: str
    soil_type: SoilTypeEnum
    size_acres: Optional[float] = None
    planting_date: Optional[date] = None
    water_source: Optional[str] = None
    seed_variety: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class FarmStatusResponse(BaseModel):
    farm_id: uuid.UUID
    status: str = Field(
        description="Latest prediction severity, or 'unknown' when no severity is available; this does not imply healthy."
    )
    latest_prediction: Optional[PredictionResponse] = None

class FarmHistoryResponse(BaseModel):
    """Farm event collections, each independently newest-first and page-limited."""

    farm_id: uuid.UUID
    readings: list[SensorReadingResponse] = Field(
        description="Sensor readings ordered newest first."
    )
    checkins: list[CheckinResponse] = Field(
        description="Image check-ins ordered newest first."
    )
    predictions: list[PredictionResponse] = Field(
        description="Predictions ordered newest first."
    )
