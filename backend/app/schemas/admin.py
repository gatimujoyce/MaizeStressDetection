from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models import ModelNameEnum
from app.schemas.farms import FarmResponse, FarmUpdate
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
    password: str = Field(min_length=8)

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

class AdminFarmUpdate(FarmUpdate):
    has_npk_sensor: Optional[bool] = None

class AuditLogEntry(BaseModel):
    id: uuid.UUID
    created_at: datetime
    admin_name: str
    action: str
    target_type: str
    target_id: Optional[uuid.UUID] = None
    target_label: str
    changes: dict = {}

    model_config = {"from_attributes": True}

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
    failure_reason: Optional[str] = None
    delivery_status: Optional[str] = None
    delivery_reported_at: Optional[datetime] = None

class SensorInstalled(BaseModel):
    has_npk_sensor: Optional[bool] = None

class SensorRequestEntry(BaseModel):
    farm_id: uuid.UUID
    farm_name: str
    location: str
    soil_type: Optional[str] = None
    size_acres: Optional[float] = None
    planting_date: Optional[date] = None
    water_source: Optional[str] = None
    seed_variety: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_npk_sensor: bool = False
    status: str = "requested"   # requested (new), in_progress, installed (completed)
    requested_at: Optional[datetime] = None
    contacted_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    note: Optional[str] = None
    farmer_id: uuid.UUID
    farmer_name: str
    farmer_phone: str


class DeviceKeyInfo(BaseModel):
    has_key: bool
    prefix: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_used_at: Optional[datetime] = None

class DeviceKeyCreated(BaseModel):
    key: str          # shown once, never stored
    prefix: str
    created_at: datetime
