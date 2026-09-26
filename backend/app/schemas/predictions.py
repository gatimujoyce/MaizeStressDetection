from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class PredictionResponse(BaseModel):
    id: uuid.UUID
    checkin_id: uuid.UUID
    reading_id: Optional[uuid.UUID] = None
    triage_result: str
    disease_label: Optional[str] = None
    disease_conf: Optional[float] = None
    sensor_label: Optional[str] = None
    sensor_conf: Optional[float] = None
    nutrient_label: Optional[str] = None
    nutrient_conf: Optional[float] = None
    severity: Optional[str] = None
    recommendation: Optional[str] = None
    model_versions: dict
    created_at: datetime

    model_config = {"from_attributes": True}

class FeedbackCreate(BaseModel):
    accurate: bool
    useful: Optional[bool] = None
    correct_label: Optional[str] = None
    comment: Optional[str] = None

class FeedbackResponse(FeedbackCreate):
    id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
