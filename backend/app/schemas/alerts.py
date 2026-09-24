from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import ChannelEnum
import uuid

class AlertResponse(BaseModel):
    id: uuid.UUID
    prediction_id: uuid.UUID
    farm_id: uuid.UUID
    severity: str
    channel: ChannelEnum
    status: str
    sent_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
