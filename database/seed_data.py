import csv
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

import config
from database.connection import engine, get_db_session
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
from utils.logging_config import configure_logging

logger = configure_logging()

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def resolve_date(raw_val: Any, as_of_date: date) -> Optional[date]:
    """Resolve a raw CSV value (integer offset or ISO string) to a date relative to as_of_date."""
    if raw_val is None:
        return None
    val_str = str(raw_val).strip()
    if not val_str:
        return None
    try:
        offset_days = int(val_str)
        return as_of_date + timedelta(days=offset_days)
    except ValueError:
        return date.fromisoformat(val_str)


def read_csv(filename: str) -> List[Dict[str, str]]:
    """Read a CSV file from the sample_data directory into a list of row dictionaries."""
    file_path = SAMPLE_DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Sample data file not found: {file_path}")
    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def seed_database(
    as_of_date: Optional[date] = None, session: Optional[Session] = None
) -> Dict[str, Dict[str, int]]:
    """Seed the database with the Northstar Services Group synthetic dataset.

    This function is completely idempotent. Stable business keys are used
    to identify existing records.
    """
    if as_of_date is None:
        as_of_date = config.DEMO_AS_OF_DATE

    if session is not None:
        return _execute_seeding(session, as_of_date)
    else:
        with get_db_session() as db:
            return _execute_seeding(db, as_of_date)


def _execute_seeding(db: Session, as_of_date: date) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}

    # 1. Departments
    dept_rows = read_csv("departments.csv")
    dept_map: Dict[str, Department] = {}
    inserted_depts, existing_depts = 0, 0
    for row in dept_rows:
        name = row["name"].strip()
        existing = db.execute(select(Department).where(Department.name == name)).scalar_one_or_none()
        if existing:
            dept_map[name] = existing
            existing_depts += 1
        else:
            dept = Department(name=name, description=row.get("description", "").strip())
            db.add(dept)
            db.flush()
            dept_map[name] = dept
            inserted_depts += 1
    summary["departments"] = {"inserted": inserted_depts, "existing": existing_depts}

    # 2. Employees
    emp_rows = read_csv("employees.csv")
    emp_map: Dict[str, Employee] = {}
    inserted_emps, existing_emps = 0, 0
    for row in emp_rows:
        email = row["email"].strip()
        dept_name = row["department_name"].strip()
        if dept_name not in dept_map:
            raise ValueError(f"Department '{dept_name}' not found for employee {email}")
        existing = db.execute(select(Employee).where(Employee.email == email)).scalar_one_or_none()
        if existing:
            emp_map[email] = existing
            existing_emps += 1
        else:
            emp = Employee(
                department_id=dept_map[dept_name].id,
                full_name=row["full_name"].strip(),
                email=email,
                is_active=row.get("is_active", "true").lower() == "true",
            )
            db.add(emp)
            db.flush()
            emp_map[email] = emp
            inserted_emps += 1
    summary["employees"] = {"inserted": inserted_emps, "existing": existing_emps}

    # 3. Management Meetings
    meeting_rows = read_csv("management_meetings.csv")
    meeting_map: Dict[str, ManagementMeeting] = {}
    inserted_meetings, existing_meetings = 0, 0
    for row in meeting_rows:
        title = row["title"].strip()
        m_date = resolve_date(row["meeting_offset_days"], as_of_date)
        assert m_date is not None
        existing = db.execute(
            select(ManagementMeeting).where(
                ManagementMeeting.title == title,
                ManagementMeeting.meeting_date == m_date,
            )
        ).scalar_one_or_none()
        if existing:
            meeting_map[title] = existing
            existing_meetings += 1
        else:
            meeting = ManagementMeeting(
                title=title,
                meeting_date=m_date,
                meeting_type=row.get("meeting_type", "Executive Review").strip(),
                status=row.get("status", "Scheduled").strip(),
            )
            db.add(meeting)
            db.flush()
            meeting_map[title] = meeting
            inserted_meetings += 1
    summary["management_meetings"] = {"inserted": inserted_meetings, "existing": existing_meetings}

    # 4. KPI Definitions
    kpi_def_rows = read_csv("kpi_definitions.csv")
    kpi_def_map: Dict[str, KPIDefinition] = {}
    inserted_kpi_defs, existing_kpi_defs = 0, 0
    for row in kpi_def_rows:
        name = row["name"].strip()
        dept_name = row.get("department_name", "").strip()
        dept_id = dept_map[dept_name].id if dept_name in dept_map else None
        existing = db.execute(
            select(KPIDefinition).where(
                KPIDefinition.name == name,
                KPIDefinition.department_id == dept_id,
            )
        ).scalar_one_or_none()
        if existing:
            kpi_def_map[name] = existing
            existing_kpi_defs += 1
        else:
            kpi_def = KPIDefinition(
                name=name,
                department_id=dept_id,
                unit=row["unit"].strip(),
                direction=row.get("direction", "Higher is better").strip(),
                is_active=row.get("is_active", "true").lower() == "true",
            )
            db.add(kpi_def)
            db.flush()
            kpi_def_map[name] = kpi_def
            inserted_kpi_defs += 1
    summary["kpi_definitions"] = {"inserted": inserted_kpi_defs, "existing": existing_kpi_defs}

    # 5. Initiatives
    init_rows = read_csv("initiatives.csv")
    init_map: Dict[str, Initiative] = {}
    inserted_inits, existing_inits = 0, 0
    for row in init_rows:
        code = row["code"].strip()
        dept_name = row["department_name"].strip()
        owner_email = row["owner_email"].strip()

        if dept_name not in dept_map:
            raise ValueError(f"Unknown department '{dept_name}' for initiative {code}")
        if owner_email not in emp_map:
            raise ValueError(f"Unknown owner '{owner_email}' for initiative {code}")

        owner = emp_map[owner_email]
        dept = dept_map[dept_name]
        if owner.department_id != dept.id:
            raise ValueError(f"Owner {owner_email} does not belong to department {dept_name}")

        start_date = resolve_date(row["start_offset_days"], as_of_date)
        target_date = resolve_date(row["target_offset_days"], as_of_date)
        assert start_date is not None and target_date is not None

        progress = int(row.get("progress_pct", 0))
        status = row.get("status", "Not Started").strip()
        if status == "Completed" and progress != 100:
            raise ValueError(f"Completed initiative {code} must have 100% progress")

        existing = db.execute(select(Initiative).where(Initiative.code == code)).scalar_one_or_none()
        if existing:
            init_map[code] = existing
            existing_inits += 1
        else:
            init = Initiative(
                code=code,
                department_id=dept.id,
                owner_id=owner.id,
                name=row["name"].strip(),
                description=row.get("description", "").strip(),
                strategic_objective=row.get("strategic_objective", "").strip(),
                expected_outcome=row.get("expected_outcome", "").strip(),
                priority=row.get("priority", "Medium").strip(),
                start_date=start_date,
                target_date=target_date,
                status=status,
                progress_pct=progress,
            )
            db.add(init)
            db.flush()
            init_map[code] = init
            inserted_inits += 1
    summary["initiatives"] = {"inserted": inserted_inits, "existing": existing_inits}

    # 6. Milestones
    ms_rows = read_csv("milestones.csv")
    inserted_ms, existing_ms = 0, 0
    for row in ms_rows:
        init_code = row["initiative_code"].strip()
        name = row["name"].strip()
        owner_email = row["owner_email"].strip()

        if init_code not in init_map:
            raise ValueError(f"Unknown initiative '{init_code}' in milestone '{name}'")
        if owner_email not in emp_map:
            raise ValueError(f"Unknown owner '{owner_email}' in milestone '{name}'")

        init = init_map[init_code]
        owner = emp_map[owner_email]

        planned_date = resolve_date(row["planned_offset_days"], as_of_date)
        actual_date = resolve_date(row.get("actual_offset_days"), as_of_date)
        status = row.get("status", "Not Started").strip()

        if status == "Completed" and actual_date is None:
            raise ValueError(f"Completed milestone '{name}' on {init_code} requires actual completion date")

        existing = db.execute(
            select(Milestone).where(
                Milestone.initiative_id == init.id,
                Milestone.name == name,
            )
        ).scalar_one_or_none()

        if existing:
            existing_ms += 1
        else:
            milestone = Milestone(
                initiative_id=init.id,
                owner_id=owner.id,
                name=name,
                planned_date=planned_date,
                actual_date=actual_date,
                status=status,
                notes=row.get("notes", "").strip(),
            )
            db.add(milestone)
            inserted_ms += 1
    db.flush()
    summary["milestones"] = {"inserted": inserted_ms, "existing": existing_ms}

    # 7. Initiative Updates
    upd_rows = read_csv("initiative_updates.csv")
    inserted_upds, existing_upds = 0, 0
    for row in upd_rows:
        init_code = row["initiative_code"].strip()
        author_email = row["author_email"].strip()

        if init_code not in init_map:
            raise ValueError(f"Unknown initiative '{init_code}' in update")
        if author_email not in emp_map:
            raise ValueError(f"Unknown author '{author_email}' in update")

        init = init_map[init_code]
        author = emp_map[author_email]
        upd_date = resolve_date(row["update_offset_days"], as_of_date)
        assert upd_date is not None
        progress = int(row["progress_pct"])
        status = row["status"].strip()
        text_content = row["update_text"].strip()

        existing = db.execute(
            select(InitiativeUpdate).where(
                InitiativeUpdate.initiative_id == init.id,
                InitiativeUpdate.update_date == upd_date,
                InitiativeUpdate.update_text == text_content,
            )
        ).scalar_one_or_none()

        if existing:
            existing_upds += 1
        else:
            update = InitiativeUpdate(
                initiative_id=init.id,
                author_id=author.id,
                update_date=upd_date,
                progress_pct=progress,
                status=status,
                update_text=text_content,
            )
            db.add(update)
            inserted_upds += 1
    db.flush()
    summary["initiative_updates"] = {"inserted": inserted_upds, "existing": existing_upds}

    # 8. Initiative Dependencies
    dep_rows = read_csv("initiative_dependencies.csv")
    inserted_deps, existing_deps = 0, 0
    for row in dep_rows:
        init_code = row["initiative_code"].strip()
        dep_code = row["depends_on_code"].strip()

        if init_code not in init_map or dep_code not in init_map:
            raise ValueError(f"Dependency reference not found: {init_code} -> {dep_code}")
        if init_code == dep_code:
            raise ValueError(f"Initiative {init_code} cannot depend on itself")

        init_id = init_map[init_code].id
        dep_id = init_map[dep_code].id

        existing = db.execute(
            select(InitiativeDependency).where(
                InitiativeDependency.initiative_id == init_id,
                InitiativeDependency.depends_on_initiative_id == dep_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing_deps += 1
        else:
            dependency = InitiativeDependency(
                initiative_id=init_id,
                depends_on_initiative_id=dep_id,
            )
            db.add(dependency)
            inserted_deps += 1
    db.flush()
    summary["initiative_dependencies"] = {"inserted": inserted_deps, "existing": existing_deps}

    # 9. Risks
    risk_rows = read_csv("risks.csv")
    inserted_risks, existing_risks = 0, 0
    for row in risk_rows:
        init_code = row["initiative_code"].strip()
        title = row["title"].strip()
        if init_code not in init_map:
            raise ValueError(f"Unknown initiative '{init_code}' in risk '{title}'")

        init = init_map[init_code]
        ident_date = resolve_date(row["identified_offset_days"], as_of_date)
        assert ident_date is not None

        existing = db.execute(
            select(Risk).where(
                Risk.initiative_id == init.id,
                Risk.title == title,
            )
        ).scalar_one_or_none()

        if existing:
            existing_risks += 1
        else:
            risk = Risk(
                initiative_id=init.id,
                title=title,
                description=row.get("description", "").strip(),
                severity=row.get("severity", "Medium").strip(),
                status=row.get("status", "Open").strip(),
                identified_date=ident_date,
            )
            db.add(risk)
            inserted_risks += 1
    db.flush()
    summary["risks"] = {"inserted": inserted_risks, "existing": existing_risks}

    # 10. Leadership Decisions
    dec_rows = read_csv("leadership_decisions.csv")
    inserted_decs, existing_decs = 0, 0
    for row in dec_rows:
        text_desc = row["decision_text"].strip()
        dec_date = resolve_date(row["decision_offset_days"], as_of_date)
        assert dec_date is not None

        existing = db.execute(
            select(LeadershipDecision).where(
                LeadershipDecision.decision_text == text_desc,
                LeadershipDecision.decision_date == dec_date,
            )
        ).scalar_one_or_none()

        if existing:
            existing_decs += 1
        else:
            init_code = row.get("initiative_code", "").strip()
            meeting_title = row.get("meeting_title", "").strip()

            init_id = init_map[init_code].id if init_code in init_map else None
            meeting_id = meeting_map[meeting_title].id if meeting_title in meeting_map else None

            decision = LeadershipDecision(
                initiative_id=init_id,
                meeting_id=meeting_id,
                decision_text=text_desc,
                decision_date=dec_date,
                status=row.get("status", "Pending").strip(),
                rationale=row.get("rationale", "").strip(),
            )
            db.add(decision)
            inserted_decs += 1
    db.flush()
    summary["leadership_decisions"] = {"inserted": inserted_decs, "existing": existing_decs}

    # 11. Leadership Actions
    act_rows = read_csv("leadership_actions.csv")
    inserted_acts, existing_acts = 0, 0
    for row in act_rows:
        owner_email = row["owner_email"].strip()
        if owner_email not in emp_map:
            raise ValueError(f"Unknown owner '{owner_email}' in leadership action")

        owner = emp_map[owner_email]
        desc = row["description"].strip()
        deadline = resolve_date(row["deadline_offset_days"], as_of_date)
        completed_date = resolve_date(row.get("completed_offset_days"), as_of_date)
        assert deadline is not None

        existing = db.execute(
            select(LeadershipAction).where(
                LeadershipAction.description == desc,
                LeadershipAction.owner_id == owner.id,
                LeadershipAction.deadline == deadline,
            )
        ).scalar_one_or_none()

        if existing:
            existing_acts += 1
        else:
            init_code = row.get("initiative_code", "").strip()
            meeting_title = row.get("meeting_title", "").strip()

            init_id = init_map[init_code].id if init_code in init_map else None
            meeting_id = meeting_map[meeting_title].id if meeting_title in meeting_map else None

            action = LeadershipAction(
                initiative_id=init_id,
                owner_id=owner.id,
                meeting_id=meeting_id,
                description=desc,
                deadline=deadline,
                priority=row.get("priority", "Medium").strip(),
                status=row.get("status", "Open").strip(),
                completed_date=completed_date,
            )
            db.add(action)
            inserted_acts += 1
    db.flush()
    summary["leadership_actions"] = {"inserted": inserted_acts, "existing": existing_acts}

    # 12. KPI Measurements
    meas_rows = read_csv("kpi_measurements.csv")
    inserted_meas, existing_meas = 0, 0
    for row in meas_rows:
        kpi_name = row["kpi_name"].strip()
        dept_name = row.get("department_name", "").strip()

        if kpi_name not in kpi_def_map:
            raise ValueError(f"Unknown KPI definition '{kpi_name}'")

        kpi_def = kpi_def_map[kpi_name]
        dept_id = dept_map[dept_name].id if dept_name in dept_map else None
        m_date = resolve_date(row["measurement_offset_days"], as_of_date)
        assert m_date is not None

        existing = db.execute(
            select(KPIMeasurement).where(
                KPIMeasurement.definition_id == kpi_def.id,
                KPIMeasurement.measurement_date == m_date,
                KPIMeasurement.department_id == dept_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing_meas += 1
        else:
            meas = KPIMeasurement(
                definition_id=kpi_def.id,
                department_id=dept_id,
                measurement_date=m_date,
                actual_value=float(row["actual_value"]),
                target_value=float(row["target_value"]) if row.get("target_value") else None,
            )
            db.add(meas)
            inserted_meas += 1
    db.flush()
    summary["kpi_measurements"] = {"inserted": inserted_meas, "existing": existing_meas}

    return summary


def main() -> None:
    """CLI entry point for database seeding."""
    logger.info("Starting database seeding for Northstar Services Group...")
    print(f"Alignly Seeding — As-Of Date: {config.DEMO_AS_OF_DATE}")
    try:
        summary = seed_database()
        print("\n" + "=" * 55)
        print(f"{'Table':<28} | {'Inserted':<10} | {'Existing':<10}")
        print("-" * 55)
        total_inserted = 0
        total_existing = 0
        for table, counts in summary.items():
            ins = counts["inserted"]
            ext = counts["existing"]
            total_inserted += ins
            total_existing += ext
            print(f"{table:<28} | {ins:<10} | {ext:<10}")
        print("=" * 55)
        print(f"{'Total':<28} | {total_inserted:<10} | {total_existing:<10}")
        print("\nSuccess: Database seeding completed successfully.")
    except Exception as e:
        logger.error("Database seeding failed: %s", e)
        print(f"\nError: Database seeding failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
