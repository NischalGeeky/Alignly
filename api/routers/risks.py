# api/routers/risks.py
"""FastAPI router for Risk CRUD operations.
All endpoints use the shared SQLite database via the session provided by
`database.connection.get_db_session`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from database import models
from database.connection import get_db_session

from api.schemas.risk import RiskCreate, RiskUpdate, RiskResponse

router = APIRouter()

# Dependency that yields a SQLAlchemy session
def get_db() -> Session:
    with get_db_session() as db:
        yield db

# ---------------------------------------------------------------------------
# Create Risk
# ---------------------------------------------------------------------------
@router.post(
    "/risks",
    response_model=RiskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_risk(risk: RiskCreate, db: Session = Depends(get_db)):
    data = risk.dict()
    # Convert string UUIDs to uuid.UUID objects
    try:
        data["initiative_id"] = uuid.UUID(str(data["initiative_id"]))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID for initiative_id")

    # Validate foreign key – initiative must exist
    if not db.get(models.Initiative, data["initiative_id"]):
        raise HTTPException(status_code=400, detail="Initiative not found")

    db_risk = models.Risk(**data)
    db.add(db_risk)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(db_risk)
    return db_risk

# ---------------------------------------------------------------------------
# List Risks (optional filtering by initiative_id)
# ---------------------------------------------------------------------------
@router.get("/risks", response_model=list[RiskResponse])
def list_risks(initiative_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Risk)
    if initiative_id is not None:
        try:
            init_uuid = uuid.UUID(initiative_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid initiative_id filter")
        query = query.filter(models.Risk.initiative_id == init_uuid)
    return query.all()

# ---------------------------------------------------------------------------
# Retrieve a single Risk
# ---------------------------------------------------------------------------
@router.get("/risks/{risk_id}", response_model=RiskResponse)
def get_risk(risk_id: str, db: Session = Depends(get_db)):
    try:
        risk_uuid = uuid.UUID(risk_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Risk not found")
    risk = db.get(models.Risk, risk_uuid)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    return risk

# ---------------------------------------------------------------------------
# Update Risk
# ---------------------------------------------------------------------------
@router.put("/risks/{risk_id}", response_model=RiskResponse)
def update_risk(risk_id: str, payload: RiskUpdate, db: Session = Depends(get_db)):
    try:
        risk_uuid = uuid.UUID(risk_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Risk not found")
    risk = db.get(models.Risk, risk_uuid)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    update_data = payload.dict(exclude_unset=True)
    # If initiative_id is being updated, validate it
    if "initiative_id" in update_data:
        try:
            update_data["initiative_id"] = uuid.UUID(str(update_data["initiative_id"]))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid initiative_id")
        if not db.get(models.Initiative, update_data["initiative_id"]):
            raise HTTPException(status_code=400, detail="Initiative not found")
    # Apply updates
    for field, value in update_data.items():
        setattr(risk, field, value)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    db.refresh(risk)
    return risk

# ---------------------------------------------------------------------------
# Delete Risk
# ---------------------------------------------------------------------------
@router.delete(
    "/risks/{risk_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_risk(risk_id: str, db: Session = Depends(get_db)):
    try:
        risk_uuid = uuid.UUID(risk_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Risk not found")
    risk = db.get(models.Risk, risk_uuid)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    db.delete(risk)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    return None

# End of file
