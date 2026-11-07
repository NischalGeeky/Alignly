# api/schemas/initiative_update.py
"""Pydantic schemas for InitiativeUpdate entity.
Only fields present in the SQLAlchemy model are exposed.
"""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator

class InitiativeUpdateBase(BaseModel):
    author_id: uuid.UUID
    update_date: date
    progress_pct: int = Field(..., ge=0, le=100)
    status: str = Field(..., max_length=30)
    update_text: str

    @validator("status")
    def status_not_empty(cls, v: str):
        if not v:
            raise ValueError("status must be a non‑empty string")
        return v

class InitiativeUpdateCreate(InitiativeUpdateBase):
    pass

class InitiativeUpdateResponse(InitiativeUpdateBase):
    id: uuid.UUID

    class Config:
        orm_mode = True
