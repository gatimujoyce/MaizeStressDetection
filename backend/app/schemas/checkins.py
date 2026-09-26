from pydantic import BaseModel
from datetime import datetime
import uuid

class CheckinResponse(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    image_path: str
    created_at: datetime

    model_config = {"from_attributes": True}
