# tests/test_kpi_calculations.py
"""Tests for KPI calculation engine (services.kpi_service).

The suite uses an in‑memory SQLite database and creates only the minimal
records required for each test case. All functions from ``kpi_service`` accept a
SQLAlchemy ``Session`` instance, so the tests pass the session explicitly – this
keeps the test environment independent from the production ``config``.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the declarative base and models
from database.connection import Base
from database import models
from services import kpi_service

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in‑memory SQLite database for each test.

    The fixture yields a SQLAlchemy ``Session`` and drops all tables after the
    test finishes.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

# Helper to create a department
def create_department(session, name):
    dept = models.Department(name=name)
    session.add(dept)
    session.flush()
    return dept

# Helper to create an employee
def create_employee(session, full_name, email, department):
    emp = models.Employee(full_name=full_name, email=email, department_id=department.id)
    session.add(emp)
    session.flush()
    return emp

# Helper to create an initiative
def create_initiative(
    session,
    code,
    name,
    department,
    owner,
    status="Not Started",
    progress_pct=0,
    start_offset=0,
    target_offset=30,
):
    today = date.today()
    ini = models.Initiative(
        code=code,
        name=name,
        department_id=department.id,
        owner_id=owner.id,
        status=status,
        progress_pct=progress_pct,
        start_date=today + timedelta(days=start_offset),
        target_date=today + timedelta(days=target_offset),
    )
    session.add(ini)
    session.flush()
    return ini

# Helper to create a milestone
def create_milestone(
    session,
    initiative,
    name,
    owner,
    planned_offset,
    status="Not Started",
    actual_offset=None,
):
    today = date.today()
    planned = today + timedelta(days=planned_offset)
    actual = None
    if actual_offset is not None:
        actual = today + timedelta(days=actual_offset)
    ms = models.Milestone(
        initiative_id=initiative.id,
        owner_id=owner.id,
        name=name,
        planned_date=planned,
        actual_date=actual,
        status=status,
    )
    session.add(ms)
    session.flush()
    return ms

# Helper to create a leadership action
def create_action(session, owner, deadline_offset, status="Open"):
    today = date.today()
    act = models.LeadershipAction(
        owner_id=owner.id,
        description="Test action",
        deadline=today + timedelta(days=deadline_offset),
        status=status,
    )
    session.add(act)
    session.flush()
    return act

# Helper to create KPI definition and measurement
def create_kpi(
    session,
    name,
    unit,
    direction,
    department=None,
    measurement_offset=0,
    actual=0.0,
    target=None,
):
    kpi_def = models.KPIDefinition(
        name=name,
        unit=unit,
        direction=direction,
        department_id=department.id if department else None,
    )
    session.add(kpi_def)
    session.flush()
    meas = models.KPIMeasurement(
        definition_id=kpi_def.id,
        department_id=department.id if department else None,
        measurement_date=date.today() + timedelta(days=measurement_offset),
        actual_value=actual,
        target_value=target,
    )
    session.add(meas)
    session.flush()
    return kpi_def, meas

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_initiative_completion_rate(db_session):
    dept = create_department(db_session, "Technology")
    emp = create_employee(db_session, "Alice", "alice@example.com", dept)
    create_initiative(db_session, "INI-001", "A", dept, emp, status="Completed", progress_pct=100)
    create_initiative(db_session, "INI-002", "B", dept, emp, status="In Progress", progress_pct=30)
    db_session.commit()
    rate = kpi_service.get_initiative_completion_rate(date.today(), db_session)
    assert rate == 50.0

def test_milestone_completion_rate(db_session):
    dept = create_department(db_session, "Finance")
    emp = create_employee(db_session, "Bob", "bob@example.com", dept)
    ini = create_initiative(db_session, "INI-010", "M1", dept, emp)
    create_milestone(db_session, ini, "M1", emp, planned_offset=0, status="Completed", actual_offset=0)
    create_milestone(db_session, ini, "M2", emp, planned_offset=1, status="In Progress")
    db_session.commit()
    rate = kpi_service.get_milestone_completion_rate(date.today(), db_session)
    assert rate == 50.0

def test_overdue_milestone_count(db_session):
    dept = create_department(db_session, "Sales & Partnerships")
    emp = create_employee(db_session, "Carol", "carol@example.com", dept)
    ini = create_initiative(db_session, "INI-020", "M3", dept, emp)
    create_milestone(db_session, ini, "Old", emp, planned_offset=-5, status="In Progress")
    create_milestone(db_session, ini, "Today", emp, planned_offset=0, status="Not Started")
    create_milestone(
        db_session,
        ini,
        "Done",
        emp,
        planned_offset=-10,
        status="Completed",
        actual_offset=-9,
    )
    db_session.commit()
    count = kpi_service.get_overdue_milestone_count(date.today(), db_session)
    assert count == 1

def test_action_closure_rate(db_session):
    dept = create_department(db_session, "People & Culture")
    emp = create_employee(db_session, "Dave", "dave@example.com", dept)
    create_action(db_session, emp, deadline_offset=5, status="Completed")
    create_action(db_session, emp, deadline_offset=-2, status="Open")
    db_session.commit()
    rate = kpi_service.get_action_closure_rate(date.today(), db_session)
    assert rate == 50.0

def test_department_completion_rates(db_session):
    tech = create_department(db_session, "Technology")
    fin = create_department(db_session, "Finance")
    emp1 = create_employee(db_session, "Eve", "eve@example.com", tech)
    emp2 = create_employee(db_session, "Frank", "frank@example.com", fin)
    create_initiative(db_session, "INI-100", "T1", tech, emp1, status="Completed", progress_pct=100)
    create_initiative(db_session, "INI-101", "T2", tech, emp1, status="In Progress", progress_pct=20)
    db_session.commit()
    results = kpi_service.get_department_completion_rates(date.today(), db_session)
    tech_res = next(r for r in results if r["department"] == "Technology")
    fin_res = next(r for r in results if r["department"] == "Finance")
    assert tech_res["completion_pct"] == 50.0
    assert fin_res["completion_pct"] is None

def test_expected_progress_cases(db_session):
    dept = create_department(db_session, "Customer Operations")
    emp = create_employee(db_session, "Grace", "grace@example.com", dept)
    today = date.today()
    ini1 = models.Initiative(
        code="INI-200",
        name="Comp",
        department_id=dept.id,
        owner_id=emp.id,
        status="Completed",
        progress_pct=100,
        start_date=today - timedelta(days=10),
        target_date=today + timedelta(days=10),
    )
    ini2 = models.Initiative(
        code="INI-201",
        name="SameDay",
        department_id=dept.id,
        owner_id=emp.id,
        status="In Progress",
        progress_pct=0,
        start_date=today,
        target_date=today,
    )
    ini3 = models.Initiative(
        code="INI-202",
        name="PreStart",
        department_id=dept.id,
        owner_id=emp.id,
        status="Not Started",
        progress_pct=0,
        start_date=today + timedelta(days=5),
        target_date=today + timedelta(days=15),
    )
    ini4 = models.Initiative(
        code="INI-203",
        name="PostTarget",
        department_id=dept.id,
        owner_id=emp.id,
        status="In Progress",
        progress_pct=0,
        start_date=today - timedelta(days=20),
        target_date=today - timedelta(days=10),
    )
    ini5 = models.Initiative(
        code="INI-204",
        name="Mid",
        department_id=dept.id,
        owner_id=emp.id,
        status="In Progress",
        progress_pct=0,
        start_date=today - timedelta(days=10),
        target_date=today + timedelta(days=10),
    )
    db_session.add_all([ini1, ini2, ini3, ini4, ini5])
    db_session.commit()
    assert kpi_service.calculate_expected_progress(ini1, today) == 100.0
    assert kpi_service.calculate_expected_progress(ini2, today) == 0.0
    assert kpi_service.calculate_expected_progress(ini3, today) == 0.0
    assert kpi_service.calculate_expected_progress(ini4, today) == 100.0
    assert kpi_service.calculate_expected_progress(ini5, today) == 50.0

def test_progress_variance(db_session):
    dept = create_department(db_session, "Technology")
    emp = create_employee(db_session, "Hank", "hank@example.com", dept)
    today = date.today()
    ini = models.Initiative(
        code="INI-300",
        name="Var",
        department_id=dept.id,
        owner_id=emp.id,
        status="In Progress",
        progress_pct=40,
        start_date=today - timedelta(days=14),
        target_date=today + timedelta(days=14),
    )
    db_session.add(ini)
    db_session.commit()
    variance = kpi_service.calculate_progress_variance(ini, today)
    assert pytest.approx(variance, 0.001) == -10.0

def test_department_kpi_performance(db_session):
    tech = create_department(db_session, "Technology")
    create_kpi(
        db_session,
        name="Response Time",
        unit="hrs",
        direction="Lower is better",
        department=tech,
        measurement_offset=-1,
        actual=4.5,
        target=3.0,
    )
    kpi_def = models.KPIDefinition(name="No Measure", unit="units", direction="Higher is better")
    db_session.add(kpi_def)
    db_session.commit()
    rows = kpi_service.get_department_kpi_performance(date.today(), db_session)
    assert len(rows) == 1
    row = rows[0]
    assert row["kpi_name"] == "Response Time"
    assert row["department"] == "Technology"
    assert row["actual_value"] == 4.5
    assert row["target_value"] == 3.0
    assert row["variance"] == 1.5
    assert row["direction"] == "Lower is better"

def test_zero_denominator_handling(db_session):
    assert kpi_service.get_initiative_completion_rate(date.today(), db_session) is None
    assert kpi_service.get_milestone_completion_rate(date.today(), db_session) is None
    assert kpi_service.get_action_closure_rate(date.today(), db_session) is None

def test_department_filtering(db_session):
    tech = create_department(db_session, "Technology")
    fin = create_department(db_session, "Finance")
    emp_t = create_employee(db_session, "Ivy", "ivy@example.com", tech)
    emp_f = create_employee(db_session, "Jack", "jack@example.com", fin)
    create_initiative(db_session, "INI-400", "TechInit", tech, emp_t, status="Completed", progress_pct=100)
    create_initiative(db_session, "INI-401", "FinInit", fin, emp_f, status="In Progress", progress_pct=20)
    db_session.commit()
    results = kpi_service.get_department_completion_rates(date.today(), db_session, department_name="Technology")
    assert len(results) == 1
    assert results[0]["department"] == "Technology"
    assert results[0]["completion_pct"] == 100.0
