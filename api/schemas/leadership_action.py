# api/schemas/leadership_action.py
"""Pydantic schemas for the LeadershipAction entity.
Only fields that exist in the SQLAlchemy model are exposed.
"""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator, ConfigDict

# Allowed values based on conventions in the model
STATUS_VALUES = {"Open", "Closed", "In Progress", "Completed"}
PRIORITY_VALUES = {"Low", "Medium", "High", "Critical"}

class LeadershipActionBase(BaseModel):
    initiative_id: Optional[uuid.UUID] = None
    owner_id: uuid.UUID
    meeting_id: Optional[uuid.UUID] = None
    description: str = Field(..., min_length=1)
    deadline: date
    priority: str = Field(default="Medium", max_length=20)
    status: str = Field(default="Open", max_length=30)
    completed_date: Optional[date] = None

    @validator("status")
    def validate_status(cls, v: str):
        if v not in STATUS_VALUES:
            raise ValueError(f"Status must be one of {STATUS_VALUES}")
        return v

    @validator("priority")
    def validate_priority(cls, v: str):
        if v not in PRIORITY_VALUES:
            raise ValueError(f"Priority must be one of {PRIORITY_VALUES}")
        return v

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class LeadershipActionCreate(LeadershipActionBase):
    pass

class LeadershipActionUpdate(BaseModel):
    initiative_id: Optional[uuid.UUID] = None
    owner_id: Optional[uuid.UUID] = None
    meeting_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    completed_date: Optional[date] = None

    @validator("status")
    def validate_status(cls, v: Optional[str]):
        if v is not None and v not in STATUS_VALUES:
            raise ValueError(f"Status must be one of {STATUS_VALUES}")
        return v

    @validator("priority")
    def validate_priority(cls, v: Optional[str]):
        if v is not None and v not in PRIORITY_VALUES:
            raise ValueError(f"Priority must be one of {PRIORITY_VALUES}")
        return v

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class LeadershipActionResponse(LeadershipActionBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
