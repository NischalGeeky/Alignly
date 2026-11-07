# api/schemas/initiative.py
"""Pydantic schemas for the Initiative entity.
Only fields that exist in the SQLAlchemy model are exposed.
"""
import uuid
from datetime import date
from typing import Optional
from pydantic import ConfigDict
from pydantic import BaseModel, Field, validator

class InitiativeBase(BaseModel):
    code: str = Field(..., max_length=50)
    department_id: uuid.UUID
    owner_id: uuid.UUID
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    strategic_objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: str = Field(default="Medium", max_length=20)
    start_date: date
    target_date: date
    status: str = Field(default="Not Started", max_length=30)
    progress_pct: int = Field(default=0, ge=0, le=100)

    @validator("target_date")
    def target_not_before_start(cls, v: date, values):
        start = values.get("start_date")
        if start and v < start:
            raise ValueError("target_date must be on or after start_date")
        return v

class InitiativeCreate(InitiativeBase):
    pass

class InitiativeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    strategic_objective: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    status: Optional[str] = None
    progress_pct: Optional[int] = None

    @validator("progress_pct")
    def progress_range(cls, v: Optional[int]):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("progress_pct must be between 0 and 100")
        return v

    @validator("target_date")
    def target_not_before_start(cls, v: Optional[date], values):
        start = values.get("start_date")
        if start and v and v < start:
            raise ValueError("target_date must be on or after start_date")
        return v

class InitiativeResponse(InitiativeBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
