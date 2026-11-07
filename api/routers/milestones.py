# api/routers/milestones.py
"""FastAPI router for Milestone CRUD operations.
All endpoints use a shared SQLite database via the session provided by
`database.connection.get_db_session`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database import models
import uuid

from api.schemas.milestone import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse,
)

router = APIRouter()

# Dependency that yields a SQLAlchemy session
def get_db() -> Session:
    with get_db_session() as db:
        yield db

@router.post(
    "/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_milestone(milestone: MilestoneCreate, db: Session = Depends(get_db)):
    # Convert string IDs to UUID objects
    data = milestone.dict()
    try:
        data["initiative_id"] = uuid.UUID(str(data["initiative_id"]))
        data["owner_id"] = uuid.UUID(str(data["owner_id"]))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID for foreign keys")
    # Validate foreign keys
    if not db.get(models.Initiative, data["initiative_id"]):
        raise HTTPException(status_code=400, detail="Initiative not found")
    if not db.get(models.Employee, data["owner_id"]):
        raise HTTPException(status_code=400, detail="Owner (employee) not found")
    db_milestone = models.Milestone(**data)
    db.add(db_milestone)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(db_milestone)
    return db_milestone

@router.get("/milestones", response_model=list[MilestoneResponse])
def list_milestones(db: Session = Depends(get_db)):
    return db.query(models.Milestone).all()

@router.get(
    "/milestones/{milestone_id}", response_model=MilestoneResponse
)
def get_milestone(milestone_id: uuid.UUID, db: Session = Depends(get_db)):
    milestone = db.get(models.Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    return milestone

@router.put(
    "/milestones/{milestone_id}", response_model=MilestoneResponse
)
def update_milestone(
    milestone_id: uuid.UUID,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
):
    milestone = db.get(models.Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    update_data = payload.dict(exclude_unset=True)
    # Convert and validate foreign keys if present
    if "initiative_id" in update_data:
        try:
            update_data["initiative_id"] = uuid.UUID(str(update_data["initiative_id"]))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid initiative_id")
        if not db.get(models.Initiative, update_data["initiative_id"]):
            raise HTTPException(status_code=400, detail="Initiative not found")
    if "owner_id" in update_data:
        try:
            update_data["owner_id"] = uuid.UUID(str(update_data["owner_id"]))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid owner_id")
        if not db.get(models.Employee, update_data["owner_id"]):
            raise HTTPException(status_code=400, detail="Owner (employee) not found")
    for field, value in update_data.items():
        setattr(milestone, field, value)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(milestone)
    return milestone

@router.delete(
    "/milestones/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_milestone(milestone_id: uuid.UUID, db: Session = Depends(get_db)):
    milestone = db.get(models.Milestone, milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    return None
