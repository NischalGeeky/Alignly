# api/routers/initiative_updates.py
"""FastAPI router for InitiativeUpdate CRUD (create & list).
Provides:
- POST /initiatives/{initiative_id}/updates
- GET  /initiatives/{initiative_id}/updates
Both endpoints rely on the shared DB session dependency defined in api.main.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database import models
from api.schemas.initiative_update import (
    InitiativeUpdateCreate,
    InitiativeUpdateResponse,
)

router = APIRouter()

def get_db() -> Session:
    with get_db_session() as db:
        yield db

@router.post(
    "/initiatives/{initiative_id}/updates",
    response_model=InitiativeUpdateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_update(
    initiative_id: str,
    update: InitiativeUpdateCreate,
    db: Session = Depends(get_db),
):
    # Verify initiative exists
    initiative = db.get(models.Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    # Verify author exists
    author = db.get(models.Employee, update.author_id)
    if not author:
        raise HTTPException(status_code=400, detail="Author (employee) not found")

    db_update = models.InitiativeUpdate(
        initiative_id=initiative_id,
        **update.dict(),
    )
    db.add(db_update)
    # Synchronize initiative's current progress and status with the latest update
    initiative.progress_pct = update.progress_pct
    initiative.status = update.status
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(db_update)
    return db_update

@router.get(
    "/initiatives/{initiative_id}/updates",
    response_model=list[InitiativeUpdateResponse],
)
def list_updates(initiative_id: str, db: Session = Depends(get_db)):
    initiative = db.get(models.Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    updates = (
        db.query(models.InitiativeUpdate)
        .filter(models.InitiativeUpdate.initiative_id == initiative_id)
        .order_by(models.InitiativeUpdate.update_date)
        .all()
    )
    return updates
