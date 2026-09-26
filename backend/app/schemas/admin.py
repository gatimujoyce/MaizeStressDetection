from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import ModelNameEnum
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
