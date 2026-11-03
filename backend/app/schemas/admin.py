from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import ModelNameEnum
from app.schemas.farms import FarmResponse
from app.schemas.predictions import FeedbackResponse
import uuid

class ModelVersionResponse(BaseModel):
    id: uuid.UUID
    model_name: ModelNameEnum
    version: str
    metrics: dict
    is_active: bool

    model_config = {"from_attributes": True}

class ModelVersionUpdate(BaseModel):
    is_active: bool

class RetrainingJobResponse(BaseModel):
    id: uuid.UUID
    model_name: str
    old_metrics: dict
    new_metrics: dict
    passed_gate: bool
    deployed: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class RetrainRequest(BaseModel):
    model_name: str

class AdminUserCreate(BaseModel):
    name: str
    phone: str
    password: str

class AdminFarmResponse(FarmResponse):
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None

class AdminFeedbackResponse(FeedbackResponse):
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    disease_label: Optional[str] = None
    severity: Optional[str] = None

class SmsLogEntry(BaseModel):
    id: uuid.UUID
    created_at: datetime
    status: str
    kind: str
    severity: Optional[str] = None
    message: str
    phone: str
    farm_id: Optional[uuid.UUID] = None
    farm_name: Optional[str] = None
    farmer_id: Optional[uuid.UUID] = None
    farmer_name: Optional[str] = None
