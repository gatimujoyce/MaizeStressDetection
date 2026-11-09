from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional
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

Matched = Literal["yes", "partly", "no"]
ActionTaken = Literal["followed", "other", "none"]
FollowUpOutcome = Literal["better", "same", "worse", "not_acted"]

class FeedbackCreate(BaseModel):
    """What the farmer says about a result. `matched` is the main answer; `accurate` follows from it
    (only a full match counts as accurate), or can be sent on its own by older callers."""
    accurate: Optional[bool] = None
    useful: Optional[bool] = None
    correct_label: Optional[str] = Field(default=None, max_length=60)
    comment: Optional[str] = Field(default=None, max_length=500)
    matched: Optional[Matched] = None
    action_taken: Optional[ActionTaken] = None

    @model_validator(mode="after")
    def fill_accurate(self):
        if self.matched is not None:
            self.accurate = self.matched == "yes"
        if self.accurate is None:
            raise ValueError("Say whether the result matched what you see")
        return self

class FeedbackResponse(FeedbackCreate):
    id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime
    follow_up_outcome: Optional[FollowUpOutcome] = None
    follow_up_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class FollowUpCreate(BaseModel):
    outcome: FollowUpOutcome

class FollowUpDue(BaseModel):
    """A result the farmer got advice about a week ago, still waiting for "How did it go?"."""
    prediction_id: uuid.UUID
    farm_id: uuid.UUID
    label: Optional[str] = None
    severity: Optional[str] = None
    advice: Optional[str] = None
    answered_at: datetime
