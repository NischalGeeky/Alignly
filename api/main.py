from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from api.routers import imports
from database.connection import get_db_session
from api.routers import initiatives, milestones, initiative_updates

app = FastAPI(
    title="Alignly API",
    version="1.0.0",
    description="REST API for managing Alignly operational data.",
)

# Allow all origins for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Dependency injection for DB session
def get_db() -> Session:
    with get_db_session() as db:
        yield db

# Include only the initiative router for now
app.include_router(initiatives.router, prefix="/api", tags=["Initiatives"], dependencies=[Depends(get_db)])
app.include_router(milestones.router, prefix="/api", tags=["Milestones"], dependencies=[Depends(get_db)])
app.include_router(initiative_updates.router, prefix="/api", tags=["Initiative Updates"], dependencies=[Depends(get_db)])
# Register imports router

app.include_router(imports.router, prefix="/api", tags=["Imports"], dependencies=[Depends(get_db)])
# Register risks router
from api.routers import risks
app.include_router(risks.router, prefix="/api", tags=["Risks"], dependencies=[Depends(get_db)])
