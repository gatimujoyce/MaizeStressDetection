from pydantic import BaseModel, Field
from typing import Optional
from app.models import SoilTypeEnum
from app.schemas.predictions import PredictionResponse
from app.schemas.checkins import CheckinResponse
from app.schemas.readings import SensorReadingResponse
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
