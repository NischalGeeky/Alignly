# tests/test_risk_api.py
"""Risk CRUD API tests.
Uses the same temporary SQLite fixture as the other API tests.
"""
import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

# Re‑use the temporary DB fixture from the existing test suite.
# It creates a temporary SQLite file, sets DATABASE_URL, runs init_db, and provides a TestClient.
@pytest.fixture(scope="session", autouse=True)
def temporary_db():
    import os, tempfile
    from database import init_db
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = tf.name
    tf.close()
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
    # Initialise tables
    init_db.main()
    # Import the FastAPI app after DB is ready
    from api.main import app
    client = TestClient(app)
    # expose client globally for other fixtures
    globals()["client"] = client
    yield db_path
    os.unlink(db_path)

# Helper to create a department & employee – same logic as in test_api
def create_department_and_employee():
    from database import models
    from database.connection import get_db_session
    with get_db_session() as db:
        unique_id = uuid.uuid4().hex[:6]
        dept = models.Department(name=f"Test Dept {unique_id}")
        db.add(dept)
        db.flush()
        emp = models.Employee(
            department_id=dept.id,
            full_name="John Doe",
            email=f"john{unique_id}@example.com",
        )
        db.add(emp)
        db.commit()
        db.refresh(dept)
        db.refresh(emp)
        return dept.id, emp.id

# Helper to create an initiative via the API (needs department_id and owner_id as strings)
def create_initiative(dept_id, emp_id):
    payload = {
        "code": f"INI-{uuid.uuid4().hex[:6]}",
        "department_id": str(dept_id),
        "owner_id": str(emp_id),
        "name": "Test Initiative",
        "description": "desc",
        "strategic_objective": "obj",
        "expected_outcome": "out",
        "priority": "Medium",
        "start_date": str(date.today()),
        "target_date": str(date.today() + timedelta(days=30)),
        "status": "Not Started",
        "progress_pct": 0,
    }
    response = client.post("/api/initiatives", json=payload)
    assert response.status_code == 201
    return response.json()["id"]

def test_create_valid_risk():
    dept_id, emp_id = create_department_and_employee()
    initiative_id = create_initiative(dept_id, emp_id)
    payload = {
        "initiative_id": str(initiative_id),
        "title": "Risk 1",
        "description": "Test risk",
        "severity": "High",
        "status": "Open",
        "identified_date": str(date.today()),
    }
    resp = client.post("/api/risks", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["severity"] == payload["severity"]
    assert data["status"] == payload["status"]
    # store for later retrieval
    global created_risk_id
    created_risk_id = data["id"]

def test_get_risk():
    resp = client.get(f"/api/risks/{created_risk_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created_risk_id

def test_list_risks():
    resp = client.get("/api/risks")
    assert resp.status_code == 200
    lst = resp.json()
    assert any(r["id"] == created_risk_id for r in lst)

def test_filter_by_initiative():
    # create a second initiative and risk
    dept_id, emp_id = create_department_and_employee()
    initiative_id2 = create_initiative(dept_id, emp_id)
    payload = {
        "initiative_id": str(initiative_id2),
        "title": "Risk 2",
        "description": "Second risk",
        "severity": "Low",
        "status": "Open",
        "identified_date": str(date.today()),
    }
    resp = client.post("/api/risks", json=payload)
    assert resp.status_code == 201
    risk2_id = resp.json()["id"]
    # filter by first initiative – should NOT include risk2
    first_init = payload["initiative_id"]  # actually this is second init; get first from earlier
    # retrieve first initiative id used in test_create_valid_risk (stored globally?)
    # We can fetch from created risk
    resp = client.get(f"/api/risks/{created_risk_id}")
    first_init_id = resp.json()["initiative_id"]
    filtered = client.get(f"/api/risks?initiative_id={first_init_id}")
    assert filtered.status_code == 200
    ids = [r["id"] for r in filtered.json()]
    assert created_risk_id in ids
    assert risk2_id not in ids

def test_update_risk():
    update_payload = {"severity": "Critical", "status": "Mitigated"}
    resp = client.put(f"/api/risks/{created_risk_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["severity"] == "Critical"
    assert data["status"] == "Mitigated"

def test_delete_risk():
    resp = client.delete(f"/api/risks/{created_risk_id}")
    assert resp.status_code == 204
    # subsequent GET should be 404
    resp2 = client.get(f"/api/risks/{created_risk_id}")
    assert resp2.status_code == 404

def test_invalid_initiative_reference():
    payload = {
        "initiative_id": str(uuid.uuid4()),
        "title": "Bad Risk",
        "severity": "Low",
        "status": "Open",
        "identified_date": str(date.today()),
    }
    resp = client.post("/api/risks", json=payload)
    assert resp.status_code == 400

def test_invalid_severity_status():
    dept_id, emp_id = create_department_and_employee()
    initiative_id = create_initiative(dept_id, emp_id)
    payload = {
        "initiative_id": str(initiative_id),
        "title": "Bad Risk",
        "severity": "Unknown",
        "status": "Open",
        "identified_date": str(date.today()),
    }
    resp = client.post("/api/risks", json=payload)
    # Pydantic validation should raise 422
    assert resp.status_code == 422

    payload["severity"] = "Low"
    payload["status"] = "Weird"
    resp2 = client.post("/api/risks", json=payload)
    assert resp2.status_code == 422

def test_get_nonexistent():
    resp = client.get(f"/api/risks/{uuid.uuid4()}")
    assert resp.status_code == 404
