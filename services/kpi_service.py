# services/kpi_service.py
"""KPI calculation engine.

All functions accept an explicit ``as_of_date`` (a :class:`datetime.date`) that
represents the reporting date for the calculation.  The functions use the
SQLAlchemy session provided by :func:`database.connection.get_db_session` unless a
session is passed explicitly – this makes the service easy to test with an
in‑memory SQLite database.

The implementation follows the formulas documented in the Alignly README
(section 8).  Wherever a division by zero could occur the function returns
``None`` to signal that the metric is unavailable; the caller can decide how to
present this.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.connection import get_db_session
from database.models import (
    Initiative,
    Milestone,
    LeadershipAction,
    Department,
    KPIDefinition,
    KPIMeasurement,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Clamp *value* between *min_value* and *max_value*.

    The KPI engine never rounds values; rounding is left to the presentation
    layer.  ``float`` is used to keep full precision for variance calculations.
    """

    return max(min_value, min(max_value, value))

# ---------------------------------------------------------------------------
# Core KPI functions
# ---------------------------------------------------------------------------

def get_initiative_completion_rate(as_of_date: date, session: Optional[Session] = None) -> Optional[float]:
    """Return the percentage of initiatives that are *Completed*.

    ``None`` is returned when there are no initiatives in the database.
    """

    sess = session or get_db_session()
    with sess:
        total = sess.execute(select(func.count()).select_from(Initiative)).scalar_one()
        if total == 0:
            return None
        completed = (
            sess.execute(
                select(func.count()).where(Initiative.status == "Completed")
            )
            .scalar_one()
        )
        return (completed / total) * 100.0


def get_milestone_completion_rate(as_of_date: date, session: Optional[Session] = None) -> Optional[float]:
    """Return the percentage of milestones that are *Completed*.

    ``None`` is returned for an empty milestone set.
    """

    sess = session or get_db_session()
    with sess:
        total = sess.execute(select(func.count()).select_from(Milestone)).scalar_one()
        if total == 0:
            return None
        completed = (
            sess.execute(select(func.count()).where(Milestone.status == "Completed"))
            .scalar_one()
        )
        return (completed / total) * 100.0


def get_overdue_milestone_count(as_of_date: date, session: Optional[Session] = None) -> int:
    """Count milestones whose *planned_date* is before ``as_of_date`` and are not completed.
    """

    sess = session or get_db_session()
    with sess:
        count = (
            sess.execute(
                select(func.count()).where(
                    Milestone.status != "Completed",
                    Milestone.planned_date < as_of_date,
                )
            )
            .scalar_one()
        )
        return int(count)


def get_action_closure_rate(as_of_date: date, session: Optional[Session] = None) -> Optional[float]:
    """Return the percentage of leadership actions that are *Completed*.

    Over‑due actions are *not* considered completed – the status column drives the
    calculation.
    """

    sess = session or get_db_session()
    with sess:
        total = sess.execute(select(func.count()).select_from(LeadershipAction)).scalar_one()
        if total == 0:
            return None
        completed = (
            sess.execute(select(func.count()).where(LeadershipAction.status == "Completed"))
            .scalar_one()
        )
        return (completed / total) * 100.0


def get_department_completion_rates(
    as_of_date: date, session: Optional[Session] = None, department_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Return a list of completion‑rate dictionaries per department.

    Each dictionary contains ``department``, ``total_initiatives``,
    ``completed_initiatives`` and ``completion_pct`` (or ``None`` when the
    department has no initiatives).
    """

    sess = session or get_db_session()
    with sess:
        dept_query = select(Department)
        if department_name:
            dept_query = dept_query.where(Department.name == department_name)
        departments = sess.execute(dept_query).scalars().all()

        results: List[Dict[str, Any]] = []
        for dept in departments:
            total = (
                sess.execute(
                    select(func.count()).where(Initiative.department_id == dept.id)
                )
                .scalar_one()
            )
            completed = (
                sess.execute(
                    select(func.count()).where(
                        Initiative.department_id == dept.id,
                        Initiative.status == "Completed",
                    )
                )
                .scalar_one()
            )
            pct = (completed / total) * 100.0 if total else None
            results.append(
                {
                    "department": dept.name,
                    "total_initiatives": total,
                    "completed_initiatives": completed,
                    "completion_pct": pct,
                }
            )
        return results


def calculate_expected_progress(initiative: Initiative, as_of_date: date) -> float:
    """Calculate the expected progress for *initiative* on ``as_of_date``.

    The rules are taken verbatim from the README.  The function always returns a
    ``float`` in the range ``0‑100``.
    """

    # Rule 1 – completed initiatives are 100 % regardless of dates
    if initiative.status == "Completed":
        return 100.0

    start = initiative.start_date
    target = initiative.target_date
    # Guard against degenerate dates (same‑day) to avoid division by zero.
    if start == target:
        # If the reporting date is before or on the start date → 0, else 100
        return 0.0 if as_of_date <= start else 100.0

    if as_of_date <= start:
        return 0.0
    if as_of_date >= target:
        return 100.0
    # Linear interpolation between start and target
    elapsed = (as_of_date - start).days
    total_days = (target - start).days
    expected = (elapsed / total_days) * 100.0
    return _clamp(expected)


def calculate_progress_variance(initiative: Initiative, as_of_date: date) -> float:
    """Return ``actual - expected`` progress for *initiative* on ``as_of_date``.
    """

    actual = float(initiative.progress_pct)
    expected = calculate_expected_progress(initiative, as_of_date)
    return actual - expected


def get_department_kpi_performance(
    as_of_date: date,
    session: Optional[Session] = None,
    department_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return KPI performance rows up to ``as_of_date``.

    Each row contains the KPI definition fields together with the latest
    measurement on or before ``as_of_date``.  If a KPI has no measurement the
    row is omitted – this mirrors the behaviour in the README examples.
    """

    sess = session or get_db_session()
    with sess:
        kpi_query = select(KPIDefinition).where(KPIDefinition.is_active == True)
        if department_name:
            kpi_query = kpi_query.join(Department).where(Department.name == department_name)
        definitions = sess.execute(kpi_query).scalars().all()

        rows: List[Dict[str, Any]] = []
        for definition in definitions:
            # Latest measurement on or before the reporting date
            meas = (
                sess.execute(
                    select(KPIMeasurement)
                    .where(
                        KPIMeasurement.definition_id == definition.id,
                        KPIMeasurement.measurement_date <= as_of_date,
                    )
                    .order_by(KPIMeasurement.measurement_date.desc())
                )
                .scalars()
                .first()
            )
            if meas is None:
                continue
            variance = meas.actual_value - (meas.target_value or 0.0)
            rows.append(
                {
                    "kpi_name": definition.name,
                    "department": (
                        definition.department.name if definition.department else None
                    ),
                    "measurement_date": meas.measurement_date,
                    "actual_value": meas.actual_value,
                    "target_value": meas.target_value,
                    "variance": variance,
                    "unit": definition.unit,
                    "direction": definition.direction,
                }
            )
        return rows

# Optional convenience wrapper used by UI code (if any).
def get_kpi_summary(*args, **kwargs):  # pragma: no cover – thin wrapper
    """Alias for ``get_department_kpi_performance`` kept for backward compatibility."""

    return get_department_kpi_performance(*args, **kwargs)
