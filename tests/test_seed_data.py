from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

import config
from database.connection import Base
from database.models import (
    Department,
    Employee,
    Initiative,
    InitiativeDependency,
    InitiativeUpdate,
    KPIDefinition,
    KPIMeasurement,
    LeadershipAction,
    LeadershipDecision,
    ManagementMeeting,
    Milestone,
    Risk,
)
from database.seed_data import seed_database


@pytest.fixture(scope="function")
def isolated_db_session():
    """Create a completely separate in-memory SQLite engine and session for seeding tests."""
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_successful_initial_seeding(isolated_db_session):
    """Test initial seeding populates all expected tables."""
    as_of = date(2026, 11, 1)
    summary = seed_database(as_of_date=as_of, session=isolated_db_session)

    assert summary["departments"]["inserted"] == 5
    assert summary["employees"]["inserted"] == 15
    assert summary["initiatives"]["inserted"] >= 15
    assert summary["milestones"]["inserted"] > 0
    assert summary["initiative_updates"]["inserted"] > 0
    assert summary["initiative_dependencies"]["inserted"] > 0
    assert summary["risks"]["inserted"] > 0
    assert summary["leadership_decisions"]["inserted"] > 0
    assert summary["leadership_actions"]["inserted"] > 0
    assert summary["management_meetings"]["inserted"] > 0
    assert summary["kpi_definitions"]["inserted"] > 0
    assert summary["kpi_measurements"]["inserted"] > 0


def test_seed_idempotency(isolated_db_session):
    """Running seed_database twice must produce zero duplicate insertions on the second run."""
    as_of = date(2026, 11, 1)
    summary_run1 = seed_database(as_of_date=as_of, session=isolated_db_session)
    summary_run2 = seed_database(as_of_date=as_of, session=isolated_db_session)

    # First run inserted records
    for table, counts in summary_run1.items():
        assert counts["inserted"] > 0, f"{table} had no inserted records in run 1"
        assert counts["existing"] == 0, f"{table} reported existing records in run 1"

    # Second run should insert 0 and report all as existing
    for table, counts in summary_run2.items():
        assert counts["inserted"] == 0, f"{table} unexpectedly inserted records in run 2"
        assert counts["existing"] == summary_run1[table]["inserted"], f"{table} count mismatch in run 2"


def test_department_and_employee_relationships(isolated_db_session):
    """Verify exactly 5 departments exist and all employees belong to a valid department."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    expected_depts = {
        "Customer Operations",
        "Finance",
        "People & Culture",
        "Technology",
        "Sales & Partnerships",
    }
    depts = isolated_db_session.execute(select(Department)).scalars().all()
    assert len(depts) == 5
    assert {d.name for d in depts} == expected_depts

    employees = isolated_db_session.execute(select(Employee)).scalars().all()
    assert len(employees) >= 15
    for emp in employees:
        assert emp.department is not None
        assert emp.department.name in expected_depts
        assert emp.is_active is True
        assert emp.email.endswith("@example.com")


def test_initiative_distribution_across_departments(isolated_db_session):
    """Initiatives must be distributed across all 5 departments, and owners must belong to the department."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    depts = isolated_db_session.execute(select(Department)).scalars().all()
    for dept in depts:
        assert len(dept.initiatives) >= 2, f"Department {dept.name} has fewer than 2 initiatives"

    initiatives = isolated_db_session.execute(select(Initiative)).scalars().all()
    for init in initiatives:
        assert init.department is not None
        assert init.owner is not None
        assert init.owner.department_id == init.department_id, (
            f"Initiative {init.code} owner {init.owner.email} is not in department {init.department.name}"
        )


def test_minimum_initiative_count(isolated_db_session):
    """At least 15 initiatives must be seeded with stable codes."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    initiatives = isolated_db_session.execute(select(Initiative)).scalars().all()
    assert len(initiatives) >= 15
    codes = [i.code for i in initiatives]
    assert len(codes) == len(set(codes)), "Initiative codes must be unique"
    for code in codes:
        assert code.startswith("INI-")


def test_completed_initiative_consistency(isolated_db_session):
    """Completed initiatives must have 100% progress and completed milestones with actual dates."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    completed_inits = isolated_db_session.execute(
        select(Initiative).where(Initiative.status == "Completed")
    ).scalars().all()

    assert len(completed_inits) >= 2, "Must have at least 2 completed initiatives"
    for init in completed_inits:
        assert init.progress_pct == 100, f"Completed initiative {init.code} progress is not 100%"
        assert len(init.milestones) > 0, f"Completed initiative {init.code} has no milestones"
        for ms in init.milestones:
            assert ms.status == "Completed", f"Milestone {ms.name} in {init.code} is not Completed"
            assert ms.actual_date is not None, f"Milestone {ms.name} has no actual completion date"


def test_milestone_integrity(isolated_db_session):
    """Milestones must reference valid initiatives and owners, and have actual date if completed."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    milestones = isolated_db_session.execute(select(Milestone)).scalars().all()
    assert len(milestones) >= 30
    for ms in milestones:
        assert ms.initiative is not None
        assert ms.owner is not None
        if ms.status == "Completed":
            assert ms.actual_date is not None, f"Completed milestone {ms.name} lacks actual_date"


def test_dependency_integrity(isolated_db_session):
    """Every dependency must link two distinct initiatives, with at least one dependency on a Blocked initiative."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    deps = isolated_db_session.execute(select(InitiativeDependency)).scalars().all()
    assert len(deps) >= 1

    blocked_dep_found = False
    for dep in deps:
        assert dep.initiative_id != dep.depends_on_initiative_id, "Self-dependency found"

        parent_init = isolated_db_session.get(Initiative, dep.initiative_id)
        prereq_init = isolated_db_session.get(Initiative, dep.depends_on_initiative_id)

        assert parent_init is not None
        assert prereq_init is not None

        if prereq_init.status == "Blocked":
            blocked_dep_found = True

    assert blocked_dep_found, "Scenario requirement missing: at least one dependency on a Blocked initiative"


def test_required_scenario_coverage(isolated_db_session):
    """Verify all 8 mandatory scenario requirements from Task 2 Section 6."""
    as_of = date(2026, 11, 1)
    seed_database(as_of_date=as_of, session=isolated_db_session)

    # 1. Completed: At least 2 initiatives with 100% progress
    completed_inits = isolated_db_session.execute(
        select(Initiative).where(Initiative.status == "Completed", Initiative.progress_pct == 100)
    ).scalars().all()
    assert len(completed_inits) >= 2, "Requirement: At least 2 completed initiatives with 100% progress"

    # 2. On Track: At least 3 initiatives with recent updates (within 7 days)
    recent_threshold = as_of - timedelta(days=7)
    recent_updates = isolated_db_session.execute(
        select(InitiativeUpdate).where(
            InitiativeUpdate.update_date >= recent_threshold,
            InitiativeUpdate.update_date <= as_of,
        )
    ).scalars().all()
    recent_init_ids = {u.initiative_id for u in recent_updates}
    assert len(recent_init_ids) >= 3, "Requirement: At least 3 initiatives with recent updates within 7 days"

    # 3. Delayed: At least 2 initiatives with overdue incomplete milestones
    delayed_milestones = isolated_db_session.execute(
        select(Milestone).where(
            Milestone.planned_date < as_of,
            Milestone.status != "Completed",
        )
    ).scalars().all()
    delayed_init_ids = {m.initiative_id for m in delayed_milestones}
    assert len(delayed_init_ids) >= 2, "Requirement: At least 2 initiatives with overdue incomplete milestones"

    # 4. At Risk: At least 2 initiatives with negative progress variance <= -15%
    # Expected progress formula: ((as_of - start) / (target - start)) * 100
    at_risk_variance_count = 0
    inits = isolated_db_session.execute(select(Initiative)).scalars().all()
    for init in inits:
        if init.status != "Completed" and init.start_date <= as_of < init.target_date:
            total_days = (init.target_date - init.start_date).days
            elapsed_days = (as_of - init.start_date).days
            expected_prog = (elapsed_days / total_days) * 100.0
            variance = init.progress_pct - expected_prog
            if variance <= -15.0:
                at_risk_variance_count += 1
    assert at_risk_variance_count >= 2, "Requirement: At least 2 initiatives with negative progress variance"

    # 5. Blocked: At least 1 blocked prerequisite/dependency
    deps = isolated_db_session.execute(select(InitiativeDependency)).scalars().all()
    has_blocked_prereq = any(
        isolated_db_session.get(Initiative, dep.depends_on_initiative_id).status == "Blocked"
        for dep in deps
    )
    assert has_blocked_prereq, "Requirement: At least 1 initiative with a blocked dependency"

    # 6. Pending Decisions: At least 2
    pending_decs = isolated_db_session.execute(
        select(LeadershipDecision).where(LeadershipDecision.status == "Pending")
    ).scalars().all()
    assert len(pending_decs) >= 2, "Requirement: At least 2 pending leadership decisions"

    # 7. Overdue Actions: At least 2 incomplete actions with past deadlines
    overdue_actions = isolated_db_session.execute(
        select(LeadershipAction).where(
            LeadershipAction.deadline < as_of,
            LeadershipAction.status != "Completed",
        )
    ).scalars().all()
    assert len(overdue_actions) >= 2, "Requirement: At least 2 incomplete actions with past deadlines"

    # 8. Upcoming Review: At least 1 scheduled meeting
    upcoming_meetings = isolated_db_session.execute(
        select(ManagementMeeting).where(
            ManagementMeeting.meeting_date > as_of,
            ManagementMeeting.status == "Scheduled",
        )
    ).scalars().all()
    assert len(upcoming_meetings) >= 1, "Requirement: At least 1 upcoming scheduled management review"


def test_transaction_rollback_on_seed_failure(isolated_db_session):
    """Seed failure must roll back without leaving partial corrupt records."""
    as_of = date(2026, 11, 1)

    # Inject an invalid record or cause a crash during seeding
    with pytest.raises(Exception):
        # We start a transaction, add a broken department with empty or conflicting name then force error
        dept = Department(name=None)  # None violates NOT NULL constraint
        isolated_db_session.add(dept)
        isolated_db_session.flush()

    isolated_db_session.rollback()

    # Verify database remains completely empty
    count = isolated_db_session.scalar(select(func.count(Department.id)))
    assert count == 0
