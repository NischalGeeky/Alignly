"""Import endpoints for Alignly.

Provides CSV/Excel import for Initiatives, Milestones, and Risks.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db_session

# Import services
from services.initiative_import_service import import_initiatives
from services.milestone_import_service import import_milestones
from services.risk_import_service import import_risks

router = APIRouter()

def get_db():
    with get_db_session() as db:
        yield db

@router.post("/imports/initiatives", tags=["Imports"], response_model=dict)
async def import_initiatives_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        summary = import_initiatives(content, file.filename, db)
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.post("/imports/milestones", tags=["Imports"], response_model=dict)
async def import_milestones_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        summary = import_milestones(content, file.filename, db)
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@router.post("/imports/risks", tags=["Imports"], response_model=dict)
async def import_risks_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        summary = import_risks(content, file.filename, db)
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
