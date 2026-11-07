# tests/test_initiative_import.py
"""Tests for Initiative CSV/Excel import endpoint.
The tests use the same temporary SQLite fixture defined in test_api.py.
"""

import io
import uuid
from datetime import date, timedelta

import pandas as pd
import pytest

# Load fixtures (temporary_db and client) from test_api
pytest_plugins = ["tests.test_api"]

@pytest.fixture(autouse=True)
def _use_tempdb(temporary_db):
    """Activate temporary DB fixture."""
    pass


@pytest.fixture
def client():
    """Expose the FastAPI TestClient from tests.test_api as a fixture.

    The ``temporary_db`` fixture from ``tests.test_api`` creates a global ``client``
    variable. Importing the module here guarantees that the fixture runs first.
    """
    import tests.test_api as test_api
    return test_api.client


def post_import(file_bytes, filename):
    """Helper to post an import file using the FastAPI TestClient.

    Imports the client from ``tests.test_api`` which is set up by the
    ``temporary_db`` fixture.
    """
    import tests.test_api as test_api
    return test_api.client.post("/api/imports/initiatives", files={"file": (filename, file_bytes)})







# Helper to create a department and employee – identical to test_api's helper.

def create_department_and_employee(db_session):
    from database import models
    unique_id = uuid.uuid4().hex[:6]
    dept = models.Department(name=f"Test Dept {unique_id}")
    db_session.add(dept)
    db_session.flush()
    emp = models.Employee(
        department_id=dept.id,
        full_name="John Doe",
        email=f"john{unique_id}@example.com",
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(dept)
    db_session.refresh(emp)
    return dept.id, emp.id

@pytest.fixture
def dept_emp_ids():
    # Use the DB session directly
    from database.connection import get_db_session
    with get_db_session() as db:
        return create_department_and_employee(db)

def build_dataframe(rows):
    """Utility to create a pandas DataFrame from list of dict rows."""
    return pd.DataFrame(rows)

def csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

def excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    # Use xlsxwriter engine which is typically available; fall back to default if not.
    try:
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
    except Exception:
        df.to_excel(buf, index=False, sheet_name="Sheet1")
    return buf.getvalue()




def test_valid_csv_import(dept_emp_ids, client):
    dept_id, emp_id = dept_emp_ids
    df = build_dataframe([
        {
            "code": "INI-001",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": "Test Initiative",
            "description": "Desc",
            "strategic_objective": "Obj",
            "expected_outcome": "Outcome",
            "priority": "High",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=30)),
            "status": "Not Started",
            "progress_pct": 0,
        }
    ])
    resp = post_import(csv_bytes(df), "initiatives.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_valid_excel_import(dept_emp_ids):
    dept_id, emp_id = dept_emp_ids
    df = build_dataframe([
        {
            "code": "INI-002",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": "Another Initiative",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=15)),
            "progress_pct": 10,
        }
    ])
    resp = post_import(excel_bytes(df), "initiatives.xlsx")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["imported"] == 1
    assert data["duplicates"] == 0
    assert data["rejected"] == 0
    assert data["errors"] == []

def test_missing_required_columns(dept_emp_ids):
    dept_id, emp_id = dept_emp_ids
    df = build_dataframe([
        {
            "department_id": str(dept_id),
            "name": "Missing Fields",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=5)),
            "progress_pct": 5,
        }
    ])
    resp = post_import(csv_bytes(df), "bad.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["rejected"] == 1
    assert any("Missing columns" in msg for err in data["errors"] for msg in err["messages"])

def test_invalid_dates_and_progress(dept_emp_ids):
    dept_id, emp_id = dept_emp_ids
    df = build_dataframe([
        {
            "code": "INI-003",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": "Bad Dates",
            "start_date": "2022-13-01",
            "target_date": "2022-12-01",
            "progress_pct": 150,
        }
    ])
    resp = post_import(csv_bytes(df), "bad2.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["rejected"] == 1
    msgs = [m for err in data["errors"] for m in err["messages"]]
    assert any("Invalid date format" in m for m in msgs)
    assert any("progress_pct must be between 0 and 100" in m for m in msgs)

def test_invalid_fk_refs(dept_emp_ids):
    df = build_dataframe([
        {
            "code": "INI-004",
            "department_id": str(uuid.uuid4()),
            "owner_id": str(uuid.uuid4()),
            "name": "Bad FK",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=10)),
            "progress_pct": 10,
        }
    ])
    resp = post_import(csv_bytes(df), "fk.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["rejected"] == 1
    msgs = [m for err in data["errors"] for m in err["messages"]]
    assert any("department_id does not reference" in m for m in msgs)
    assert any("owner_id does not reference" in m for m in msgs)

def test_duplicate_within_file(dept_emp_ids):
    dept_id, emp_id = dept_emp_ids
    rows = []
    for i in range(2):
        rows.append({
            "code": "DUP001",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": f"Dup {i}",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=5)),
            "progress_pct": 0,
        })
    df = build_dataframe(rows)
    resp = post_import(csv_bytes(df), "dup.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["imported"] == 1
    assert data["duplicates"] == 1
    assert data["rejected"] == 0

def test_duplicate_against_db(dept_emp_ids):
    dept_id, emp_id = dept_emp_ids
    df1 = build_dataframe([
        {
            "code": "EXIST001",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": "Existing",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=10)),
            "progress_pct": 0,
        }
    ])
    resp1 = post_import(csv_bytes(df1), "first.csv")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["imported"] == 1

    df2 = build_dataframe([
        {
            "code": "EXIST001",
            "department_id": str(dept_id),
            "owner_id": str(emp_id),
            "name": "Duplicate DB",
            "start_date": str(date.today()),
            "target_date": str(date.today() + timedelta(days=10)),
            "progress_pct": 0,
        }
    ])
    resp2 = post_import(csv_bytes(df2), "second.csv")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 1
    assert data2["duplicates"] == 1
    assert data2["imported"] == 0
    assert data2["rejected"] == 0

def test_empty_file():
    resp = post_import(b"", "empty.csv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["imported"] == 0
    assert data["duplicates"] == 0
    assert data["rejected"] == 0

def test_unsupported_file_type():
    resp = post_import(b"some content", "bad.txt")
    assert resp.status_code == 400
    assert "Unsupported file extension" in resp.json()["detail"]
