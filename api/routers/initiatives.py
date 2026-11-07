# api/routers/initiatives.py
"""FastAPI router for Initiative CRUD operations.
All endpoints use the shared SQLite database via the session
provided by ``database.connection.get_db_session``.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db_session
import uuid

from api.schemas.initiative import InitiativeCreate, InitiativeUpdate, InitiativeResponse

router = APIRouter()

# Dependency that yields a SQLAlchemy session
def get_db() -> Session:
    with get_db_session() as db:
        yield db

@router.post("/initiatives", response_model=InitiativeResponse, status_code=status.HTTP_201_CREATED)
def create_initiative(initiative: InitiativeCreate, db: Session = Depends(get_db)):
    # Convert string IDs to UUID objects
    data = initiative.dict()
    try:
        data["department_id"] = uuid.UUID(str(data["department_id"]))
        data["owner_id"] = uuid.UUID(str(data["owner_id"]))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID for foreign keys")
    # Validate foreign keys
    department = db.get(models.Department, data["department_id"])
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")
    owner = db.get(models.Employee, data["owner_id"])
    if not owner:
        raise HTTPException(status_code=400, detail="Owner (employee) not found")
    # Create model instance
    db_initiative = models.Initiative(**data)
    db.add(db_initiative)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(db_initiative)
    return db_initiative
    # Validate foreign keys
    department = db.get(models.Department, initiative.department_id)
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")
    owner = db.get(models.Employee, initiative.owner_id)
    if not owner:
        raise HTTPException(status_code=400, detail="Owner (employee) not found")
    # Create model instance
    db_initiative = models.Initiative(**initiative.dict())
    db.add(db_initiative)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(db_initiative)
    return db_initiative

@router.get("/initiatives", response_model=list[InitiativeResponse])
def list_initiatives(db: Session = Depends(get_db)):
    initiatives = db.query(models.Initiative).all()
    return initiatives

@router.get("/initiatives/{initiative_id}", response_model=InitiativeResponse)
def get_initiative(initiative_id: str, db: Session = Depends(get_db)):
    try:
        initiative_uuid = uuid.UUID(initiative_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Initiative not found")
    initiative = db.get(models.Initiative, initiative_uuid)

    initiative = db.get(models.Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    return initiative

@router.put("/initiatives/{initiative_id}", response_model=InitiativeResponse)
def update_initiative(initiative_id: str, payload: InitiativeUpdate, db: Session = Depends(get_db)):
    try:
        initiative_uuid = uuid.UUID(initiative_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Initiative not found")
    initiative = db.get(models.Initiative, initiative_uuid)

    initiative = db.get(models.Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    update_data = payload.dict(exclude_unset=True)
    # Validate dates if both provided
    if "start_date" in update_data and "target_date" in update_data:
        if update_data["target_date"] < update_data["start_date"]:
            raise HTTPException(status_code=400, detail="target_date must be on or after start_date")
    for field, value in update_data.items():
        setattr(initiative, field, value)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(initiative)
    return initiative

@router.delete("/initiatives/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_initiative(initiative_id: str, db: Session = Depends(get_db)):
    try:
        initiative_uuid = uuid.UUID(initiative_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Initiative not found")
    initiative = db.get(models.Initiative, initiative_uuid)

    initiative = db.get(models.Initiative, initiative_id)
    if not initiative:
        raise HTTPException(status_code=404, detail="Initiative not found")
    db.delete(initiative)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    return None
