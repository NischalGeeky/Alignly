"""Tests for Risk CSV/Excel import endpoint.
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

    Imports the client from ``tests.test_api`` which is set up by the
    ``temporary_db`` fixture.
    """
    import tests.test_api as test_api
    return test_api.client.post("/api/imports/risks", files={"file": (filename, file_bytes)})

# Helper to create a department, employee, and initiative for the tests
def create_department_employee_initiative(db_session):
    from database import models
    # Department & Employee
    unique_id = uuid.uuid4().hex[:6]
    dept = models.Department(name=f"Test Dept {unique_id}")
    db_session.add(dept)
    db_session.flush()
    emp = models.Employee(department_id=dept.id, full_name="John Doe", email=f"john{unique_id}@example.com")
    db_session.add(emp)
    db_session.flush()
    # Initiative
    initiative = models.Initiative(
        code=f"INI-{unique_id}",
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
    db_session.add(initiative)
    db_session.flush()
    return dept.id, emp.id, initiative.id

def build_dataframe(rows):
    """Utility to create a pandas DataFrame from list of dict rows."""
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
    """Create department, employee, and initiative and return their IDs."""
    from database.connection import get_db_session
    with get_db_session() as db:
        dept_id, emp_id, init_id = create_department_employee_initiative(db)
        return dept_id, emp_id, init_id

# ------------------- Test Cases -------------------

def test_valid_csv_import(initiative_info):
    dept_id, emp_id, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk A",
            "severity": "High",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "risks.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_valid_excel_import(initiative_info):
    dept_id, emp_id, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk B",
            "severity": "Low",
            "status": "Mitigated",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(excel_bytes(df), "risks.xlsx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_missing_required_columns(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            # title missing
            "severity": "Low",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "bad.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["rejected"] == 1
    assert any("Missing required field 'title'" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_severity(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk C",
            "severity": "Unknown",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "bad_sev.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("severity must be one of" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_status(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk D",
            "severity": "Low",
            "status": "Weird",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "bad_status.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("status must be one of" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_initiative_reference():
    # Use a random UUID not present
    df = build_dataframe([
        {
            "initiative_id": str(uuid.uuid4()),
            "title": "Risk X",
            "severity": "Low",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "bad_init.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("initiative_id does not reference" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_identified_date(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk Y",
            "severity": "Medium",
            "status": "Open",
            "identified_date": "2022-13-01",
        }
    ])
    resp = post_import(csv_bytes(df), "bad_date.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rejected"] == 1
    assert any("Invalid date format" in msg for err in data["errors"] for msg in err["messages"])

def test_duplicate_within_file(initiative_info):
    _, _, init_id = initiative_info
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk Z",
            "severity": "Low",
            "status": "Open",
            "identified_date": str(date.today()),
        },
        {
            "initiative_id": str(init_id),
            "title": "Risk Z",
            "severity": "Low",
            "status": "Open",
            "identified_date": str(date.today()),
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
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Risk Existing",
            "severity": "High",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    # First import succeeds
    first = post_import(csv_bytes(df), "first.csv")
    assert first.status_code == 200
    assert first.json()["imported"] == 1
    # Second import should be duplicate
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
    df = build_dataframe([
        {
            "initiative_id": str(init_id),
            "title": "Persisted Risk",
            "severity": "Critical",
            "status": "Open",
            "identified_date": str(date.today()),
        }
    ])
    resp = post_import(csv_bytes(df), "persist.csv")
    assert resp.status_code == 200
    assert resp.json()["imported"] == 1
    # Verify in DB
    from database.connection import get_db_session
    from database import models
    with get_db_session() as db:
        risk = db.query(models.Risk).filter(models.Risk.title == "Persisted Risk").first()
        assert risk is not None
        assert risk.severity == "Critical"
        assert risk.status == "Open"
