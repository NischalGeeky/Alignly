# api/schemas/milestone.py
"""Pydantic schemas for the Milestone entity.
Only fields that exist in the SQLAlchemy model are exposed.
"""
import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator

class MilestoneBase(BaseModel):
    initiative_id: uuid.UUID
    owner_id: uuid.UUID
    name: str = Field(..., max_length=200)
    planned_date: date
    actual_date: Optional[date] = None
    status: str = Field(default="Not Started", max_length=30)
    notes: Optional[str] = None

    @validator("status")
    def status_allowed(cls, v: str):
        # Basic validation – accept any non‑empty string; could be extended
        if not v:
            raise ValueError("status must be a non‑empty string")
        return v

    @validator("actual_date")
    def completed_requires_actual(cls, v: Optional[date], values):
        status = values.get("status")
        if status == "Completed" and v is None:
            raise ValueError("actual_date must be provided when status is 'Completed'")
        return v

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneUpdate(BaseModel):
    name: Optional[str] = None
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @validator("status")
    def status_allowed(cls, v: Optional[str]):
        if v is not None and not v:
            raise ValueError("status must be a non‑empty string")
        return v

    @validator("actual_date")
    def completed_requires_actual(cls, v: Optional[date], values):
        status = values.get("status")
        if status == "Completed" and v is None:
            raise ValueError("actual_date must be provided when status is 'Completed'")
        return v

class MilestoneResponse(MilestoneBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
