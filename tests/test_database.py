import uuid
from datetime import date
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database.models import (
    Department,
    Employee,
    Initiative,
    Milestone,
    InitiativeDependency,
    ManagementMeeting,
    LeadershipAction,
    LeadershipDecision,
    KPIDefinition,
    KPIMeasurement,
)

def test_engine_and_session(db_session, test_engine):
    """Verify test engine and session creation and teardown."""
    assert test_engine is not None
    assert db_session is not None
    assert db_session.is_active

def test_department_creation_and_retrieval(db_session):
    """Test creating and retrieving a department."""
    dept = Department(name="Engineering", description="Engineering and Technology")
    db_session.add(dept)
    db_session.flush()

    retrieved = db_session.execute(
        select(Department).where(Department.name == "Engineering")
    ).scalar_one_or_none()

    assert retrieved is not None
    assert retrieved.name == "Engineering"
    assert retrieved.id == dept.id

def test_department_unique_name_constraint(db_session):
    """Department names must be unique."""
    dept1 = Department(name="Product")
    db_session.add(dept1)
    db_session.flush()

    dept2 = Department(name="Product")
    db_session.add(dept2)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_employee_creation_and_relationship(db_session):
    """Test employee creation, department relationship, and email uniqueness."""
    dept = Department(name="Operations")
    db_session.add(dept)
    db_session.flush()

    emp = Employee(
        department_id=dept.id,
        full_name="Jane Doe",
        email="jane.doe@example.com",
    )
    db_session.add(emp)
    db_session.flush()

    # Relationship checks
    assert emp.department.name == "Operations"
    assert len(dept.employees) == 1
    assert dept.employees[0].email == "jane.doe@example.com"

    # Duplicate email should fail
    emp_dup = Employee(
        department_id=dept.id,
        full_name="Jane Twin",
        email="jane.doe@example.com",
    )
    db_session.add(emp_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_initiative_creation_and_unique_code(db_session):
    """Test initiative creation and unique code constraint."""
    dept = Department(name="Finance")
    db_session.add(dept)
    db_session.flush()

    emp = Employee(department_id=dept.id, full_name="John Smith", email="john.smith@example.com")
    db_session.add(emp)
    db_session.flush()

    init1 = Initiative(
        code="INI-0001",
        name="ERP Upgrade",
        department_id=dept.id,
        owner_id=emp.id,
        start_date=date(2026, 1, 1),
        target_date=date(2026, 6, 30),
        progress_pct=25,
    )
    db_session.add(init1)
    db_session.flush()

    # Duplicate initiative code must violate unique constraint
    init2 = Initiative(
        code="INI-0001",
        name="ERP Phase 2",
        department_id=dept.id,
        owner_id=emp.id,
        start_date=date(2026, 1, 1),
        target_date=date(2026, 6, 30),
        progress_pct=10,
    )
    db_session.add(init2)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_initiative_progress_range_constraint(db_session):
    """Initiative progress must be between 0 and 100."""
    dept = Department(name="Legal")
    db_session.add(dept)
    db_session.flush()

    emp = Employee(department_id=dept.id, full_name="Alice Brown", email="alice.brown@example.com")
    db_session.add(emp)
    db_session.flush()

    # Test progress > 100
    invalid_init = Initiative(
        code="INI-INVALID",
        name="Invalid Progress Initiative",
        department_id=dept.id,
        owner_id=emp.id,
        start_date=date(2026, 1, 1),
        target_date=date(2026, 6, 30),
        progress_pct=120,
    )
    db_session.add(invalid_init)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_milestone_completed_date_constraint(db_session):
    """Completed milestone must have an actual completion date."""
    dept = Department(name="HR")
    db_session.add(dept)
    db_session.flush()

    emp = Employee(department_id=dept.id, full_name="Bob Green", email="bob.green@example.com")
    db_session.add(emp)
    db_session.flush()

    init = Initiative(
        code="INI-HR-01",
        name="HR Revamp",
        department_id=dept.id,
        owner_id=emp.id,
        start_date=date(2026, 1, 1),
        target_date=date(2026, 6, 30),
        progress_pct=0,
    )
    db_session.add(init)
    db_session.flush()

    # Completed milestone without actual_date should fail check constraint
    milestone = Milestone(
        initiative_id=init.id,
        owner_id=emp.id,
        name="Policy Draft",
        planned_date=date(2026, 2, 1),
        status="Completed",
        actual_date=None,
    )
    db_session.add(milestone)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_initiative_self_dependency_constraint(db_session):
    """An initiative cannot depend on itself."""
    dept = Department(name="Marketing")
    db_session.add(dept)
    db_session.flush()

    emp = Employee(department_id=dept.id, full_name="Carla Blue", email="carla.blue@example.com")
    db_session.add(emp)
    db_session.flush()

    init = Initiative(
        code="INI-MKTG-01",
        name="Brand Launch",
        department_id=dept.id,
        owner_id=emp.id,
        start_date=date(2026, 1, 1),
        target_date=date(2026, 6, 30),
        progress_pct=0,
    )
    db_session.add(init)
    db_session.flush()

    self_dep = InitiativeDependency(
        initiative_id=init.id,
        depends_on_initiative_id=init.id,
    )
    db_session.add(self_dep)
    with pytest.raises(IntegrityError):
        db_session.flush()

def test_foreign_key_integrity(db_session):
    """Test that non-existent foreign keys are rejected."""
    non_existent_uuid = uuid.uuid4()
    emp = Employee(
        department_id=non_existent_uuid,
        full_name="Ghost User",
        email="ghost@example.com",
    )
    db_session.add(emp)
    with pytest.raises(IntegrityError):
        db_session.flush()
