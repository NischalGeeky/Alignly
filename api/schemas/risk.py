# api/schemas/risk.py
"""Pydantic schemas for the Risk entity.
Only fields that exist in the SQLAlchemy model are exposed.
"""

import uuid
from datetime import date
from typing import Optional, Literal

from pydantic import BaseModel, Field, validator, ConfigDict

# Allowed values based on model conventions
SEVERITY_LEVELS = {"Low", "Medium", "High", "Critical"}
STATUS_VALUES = {"Open", "Mitigated", "Closed"}

class RiskBase(BaseModel):
    initiative_id: uuid.UUID
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    severity: str = Field(..., max_length=30)
    status: str = Field(default="Open", max_length=30)
    identified_date: date

    @validator("severity")
    def validate_severity(cls, v: str):
        if v not in SEVERITY_LEVELS:
            raise ValueError(f"Severity must be one of {SEVERITY_LEVELS}")
        return v

    @validator("status")
    def validate_status(cls, v: str):
        if v not in STATUS_VALUES:
            raise ValueError(f"Status must be one of {STATUS_VALUES}")
        return v

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class RiskCreate(RiskBase):
    pass

class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    identified_date: Optional[date] = None

    @validator("severity")
    def validate_severity(cls, v: Optional[str]):
        if v is not None and v not in SEVERITY_LEVELS:
            raise ValueError(f"Severity must be one of {SEVERITY_LEVELS}")
        return v

    @validator("status")
    def validate_status(cls, v: Optional[str]):
        if v is not None and v not in STATUS_VALUES:
            raise ValueError(f"Status must be one of {STATUS_VALUES}")
        return v

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

class RiskResponse(RiskBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
