"""Tests for Milestone CSV/Excel import endpoint.
Uses the temporary SQLite fixture defined in tests.test_api.
"""

import io
import uuid
from datetime import date, timedelta

import pandas as pd
import pytest

# Load fixtures (temporary_db and client) from test_api
pytest_plugins = ["tests.test_api"]

# Ensure temporary_db fixture runs for this module (autouse)
@pytest.fixture(autouse=True)
def _use_tempdb(temporary_db):
    """Activate temporary DB fixture."""
    pass

# Provide FastAPI TestClient fixture
@pytest.fixture
def client():
    """Expose the FastAPI TestClient from tests.test_api.

    The ``temporary_db`` fixture from ``tests.test_api`` creates a global ``client``
    variable. Importing the module here guarantees that fixture runs first.
    """
    import tests.test_api as test_api
    return test_api.client

# Helper to post import file
def post_import(file_bytes, filename):
    """Helper to post an import file using the FastAPI TestClient.
    """
    import tests.test_api as test_api
    return test_api.client.post("/api/imports/milestones", files={"file": (filename, file_bytes)})

# Helper to create department, employee, and initiative for tests
def create_department_employee_initiative(db_session):
    from database import models
    uid = uuid.uuid4().hex[:6]
    dept = models.Department(name=f"Test Dept {uid}")
    db_session.add(dept)
    db_session.flush()
    emp = models.Employee(department_id=dept.id, full_name="John Doe", email=f"john{uid}@example.com")
    db_session.add(emp)
    db_session.flush()
    init = models.Initiative(
        code=f"INI-{uid}",
        department_id=dept.id,
        owner_id=emp.id,
        name="Test Initiative",
        description="Desc",
        strategic_objective="Obj",
        expected_outcome="Outcome",
        priority="Medium",
        start_date=date.today(),
        target_date=date.today() + timedelta(days=30),
        status="Not Started",
        progress_pct=0,
    )
    db_session.add(init)
    db_session.flush()
    return dept.id, emp.id, init.id

def build_dataframe(rows):
    return pd.DataFrame(rows)

def csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

def excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
    except Exception:
        df.to_excel(buf, index=False, sheet_name="Sheet1")
    return buf.getvalue()

@pytest.fixture
def initiative_info():
    from database.connection import get_db_session
    with get_db_session() as db:
        dept_id, emp_id, init_id = create_department_employee_initiative(db)
        return dept_id, emp_id, init_id

# ------------------- Test Cases -------------------

def test_valid_csv_import(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(uuid.uuid4()),  # placeholder owner, will be validated later
            "name": "Milestone A",
            "planned_date": str(date.today()),
            "status": "Not Started",
        }
    ])
    # Use a valid owner from the same initiative's owner
    # Retrieve the owner id
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df.at[0, "owner_id"] = str(owner_id)
    resp = post_import(csv_bytes(df), "milestones.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_valid_excel_import(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Milestone B",
            "planned_date": str(date.today()),
            "status": "Completed",
            "actual_date": str(date.today()),
        }
    ])
    resp = post_import(excel_bytes(df), "milestones.xlsx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_missing_required_columns(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            # name missing
            "planned_date": str(date.today()),
            "status": "Not Started",
        }
    ])
    resp = post_import(csv_bytes(df), "bad.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["rejected"] == 1
    assert any("Missing required field 'name'" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_dates_and_status(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Milestone Bad",
            "planned_date": "2022-13-01",
            "status": "Unknown",
        }
    ])
    resp = post_import(csv_bytes(df), "bad2.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("Invalid date format" in msg for err in data["errors"] for msg in err["messages"])
    assert any("status must be" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_initiative_reference():
    df = build_dataframe([
        {
            "initiative_id": str(uuid.uuid4()),
            "owner_id": str(uuid.uuid4()),
            "name": "Milestone X",
            "planned_date": str(date.today()),
            "status": "Not Started",
        }
    ])
    resp = post_import(csv_bytes(df), "bad_init.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("initiative_id does not reference" in msg for err in data["errors"] for msg in err["messages"])

def test_duplicate_within_file(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Dup Milestone",
            "planned_date": str(date.today()),
            "status": "Not Started",
        },
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Dup Milestone",
            "planned_date": str(date.today()),
            "status": "Not Started",
        },
    ])
    resp = post_import(csv_bytes(df), "dup.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["duplicates"] == 1
    assert data["imported"] == 1
    assert data["rejected"] == 0

def test_duplicate_against_db(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Existing Milestone",
            "planned_date": str(date.today()),
            "status": "Not Started",
        }
    ])
    # First import
    first = post_import(csv_bytes(df), "first.csv")
    assert first.status_code == 200
    assert first.json()["imported"] == 1
    # Second import (duplicate)
    second = post_import(csv_bytes(df), "second.csv")
    assert second.status_code == 200
    data = second.json()
    assert data["duplicates"] == 1
    assert data["imported"] == 0
    assert data["rejected"] == 0

def test_empty_file():
    resp = post_import(b"", "empty.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"total": 0, "imported": 0, "duplicates": 0, "rejected": 0, "errors": []}

def test_unsupported_file_type():
    resp = post_import(b"some text", "file.txt")
    assert resp.status_code == 400
    assert "Unsupported file extension" in resp.json()["detail"]

def test_persistence(initiative_info):
    _, _, init_id = initiative_info
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        owner_id = db.query(models.Initiative).filter(models.Initiative.id == uuid.UUID(str(init_id))).first().owner_id
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "owner_id": str(owner_id),
            "name": "Persisted Milestone",
            "planned_date": str(date.today()),
            "status": "Not Started",
        }
    ])
    resp = post_import(csv_bytes(df), "persist.csv")
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1
    # Verify in DB
    with get_db_session() as db:
        milestone = db.query(models.Milestone).filter(models.Milestone.name == "Persisted Milestone").first()
        assert milestone is not None
        assert milestone.status == "Not Started"
