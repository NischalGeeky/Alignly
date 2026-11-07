# pages/dashboard.py
"""Executive Command Center Dashboard.

This Streamlit page builds on the existing application, the KPI service and the
seeded SQLite/PostgreSQL database.  It provides a read‑only executive view with
KPIs, charts, tables and interactive filters.
"""

import streamlit as st
from datetime import date
from sqlalchemy import func, select
try:
    from plotly import graph_objects as go  # type: ignore
except ImportError:
    go = None  # Plotly not available; charts will be skipped gracefully

from database.connection import get_db_session
from database import models
from services import kpi_service
import config

# ---------------------------------------------------------------------------
# Helper utilities for filtered queries
# ---------------------------------------------------------------------------

def _apply_department_filter(query, department_name, session):
    if department_name and department_name != "All":
        dept = (
            session.execute(select(models.Department).where(models.Department.name == department_name))
            .scalar_one_or_none()
        )
        if dept:
            query = query.where(models.Initiative.department_id == dept.id)
    return query

def _apply_status_filter(query, status):
    if status and status != "All":
        query = query.where(models.Initiative.status == status)
    return query

# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Alignly — Executive Command Center", layout="wide")
    st.title("Executive Command Center")

    # -----------------------------------------------------------------------
    # Sidebar filters
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.header("Filters")
        # Reporting date – defaults to the demo date configured in the env
        as_of_date = st.date_input("Reporting date", config.DEMO_AS_OF_DATE)
        # Department selection – loaded from DB
        with get_db_session() as sess:
            dept_names = ["All"] + [d.name for d in sess.execute(select(models.Department).order_by(models.Department.name)).scalars().all()]
        department = st.selectbox("Department", options=dept_names)
        # Initiative status filter
        status_options = ["All", "Not Started", "In Progress", "At Risk", "Blocked", "Completed"]
        initiative_status = st.selectbox("Initiative status", options=status_options)

    # -----------------------------------------------------------------------
    # Data extraction – all queries go through a single session for consistency
    # -----------------------------------------------------------------------
    with get_db_session() as session:
        # -------------------------------------------------------------------
        # KPI cards
        # -------------------------------------------------------------------
        total_initiatives_q = select(func.count()).select_from(models.Initiative)
        total_initiatives_q = _apply_department_filter(total_initiatives_q, department, session)
        total_initiatives = session.execute(total_initiatives_q).scalar_one()

        at_risk_q = select(func.count()).where(models.Initiative.status == "At Risk")
        at_risk_q = _apply_department_filter(at_risk_q, department, session)
        at_risk_initiatives = session.execute(at_risk_q).scalar_one()

        completion_rate = kpi_service.get_initiative_completion_rate(as_of_date, session)
        overdue_milestones = kpi_service.get_overdue_milestone_count(as_of_date, session)
        action_closure_rate = kpi_service.get_action_closure_rate(as_of_date, session)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Initiatives", total_initiatives)
        col2.metric(
            "Completion Rate",
            f"{completion_rate:.1f}%" if completion_rate is not None else "N/A",
        )
        col3.metric(
            "Overdue Milestones",
            overdue_milestones,
        )
        col4.metric(
            "Action Closure Rate",
            f"{action_closure_rate:.1f}%" if action_closure_rate is not None else "N/A",
        )
        col5.metric("At‑Risk Initiatives", at_risk_initiatives)

        st.divider()

        # -------------------------------------------------------------------
        # Visualisations
        # -------------------------------------------------------------------
        # 1️⃣ Initiative health distribution (donut)
        health_counts = (
            session.query(models.Initiative.status, func.count())
            .group_by(models.Initiative.status)
            .all()
        )
        if health_counts:
            if go:
                labels, values = zip(*health_counts)
                fig_health = go.Figure(
                    data=[go.Pie(labels=labels, values=values, hole=0.5, sort=False)]
                )
                fig_health.update_layout(title_text="Initiative Health Distribution")
                st.plotly_chart(fig_health, use_container_width=True)
            else:
                st.info("Plotly not installed; initiative health chart omitted.")
        else:
            st.info("No initiatives to display.")

        # 2️⃣ Department‑wise completion rate (bar)
        dept_rates = kpi_service.get_department_completion_rates(as_of_date, session)
        if department != "All":
            dept_rates = [r for r in dept_rates if r["department"] == department]
        if dept_rates:
            fig_dept = go.Figure(
                data=[
                    go.Bar(
                        x=[r["department"] for r in dept_rates],
                        y=[r["completion_pct"] or 0 for r in dept_rates],
                        text=["—" if r["completion_pct"] is None else f"{r['completion_pct']:.1f}%" for r in dept_rates],
                        textposition="auto",
                        marker_color="#1E293B",
                    )
                ]
            )
            fig_dept.update_layout(title_text="Department Completion Rate")
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No department KPI data available.")

        # 3️⃣ Actual vs Expected initiative progress (grouped bar)
        initiative_q = select(models.Initiative).order_by(models.Initiative.code).limit(10)
        initiative_q = _apply_department_filter(initiative_q, department, session)
        initiative_q = _apply_status_filter(initiative_q, initiative_status)
        initiatives = session.execute(initiative_q).scalars().all()
        if initiatives:
            codes = [i.code for i in initiatives]
            actual = [i.progress_pct for i in initiatives]
            expected = [kpi_service.calculate_expected_progress(i, as_of_date) for i in initiatives]
            fig_prog = go.Figure()
            fig_prog.add_trace(
                go.Bar(name="Actual", x=codes, y=actual, marker_color="#2563EB")
            )
            fig_prog.add_trace(
                go.Bar(name="Expected", x=codes, y=expected, marker_color="#64748B")
            )
            fig_prog.update_layout(barmode="group", title_text="Actual vs Expected Progress")
            st.plotly_chart(fig_prog, use_container_width=True)
        else:
            st.info("No initiatives match the selected filters.")

        # 4️⃣ Milestone status distribution (donut)
        milestone_counts = (
            session.query(models.Milestone.status, func.count())
            .group_by(models.Milestone.status)
            .all()
        )
        if milestone_counts:
            labels_m, values_m = zip(*milestone_counts)
            fig_milestones = go.Figure(
                data=[go.Pie(labels=labels_m, values=values_m, hole=0.5, sort=False)]
            )
            fig_milestones.update_layout(title_text="Milestone Status Distribution")
            st.plotly_chart(fig_milestones, use_container_width=True)
        else:
            st.info("No milestones to display.")

        st.divider()

        # -------------------------------------------------------------------
        # Tabular sections
        # -------------------------------------------------------------------
        # Upcoming milestone deadlines (next 5)
        upcoming_ms = (
            session.query(models.Milestone)
            .where(models.Milestone.planned_date >= as_of_date)
            .order_by(models.Milestone.planned_date)
            .limit(5)
            .all()
        )
        if upcoming_ms:
            st.subheader("Upcoming Milestones")
            data_up = [
                {
                    "Initiative": ms.initiative.name,
                    "Milestone": ms.name,
                    "Planned": ms.planned_date,
                    "Owner": ms.owner.full_name,
                }
                for ms in upcoming_ms
            ]
            st.table(data_up)
        else:
            st.info("No upcoming milestones.")

        # Overdue leadership actions (deadline past and not completed)
        overdue_actions = (
            session.query(models.LeadershipAction)
            .where(models.LeadershipAction.deadline < as_of_date)
            .where(models.LeadershipAction.status != "Completed")
            .order_by(models.LeadershipAction.deadline)
            .all()
        )
        if overdue_actions:
            st.subheader("Overdue Leadership Actions")
            data_actions = [
                {
                    "Description": a.description,
                    "Owner": a.owner.full_name,
                    "Deadline": a.deadline,
                    "Status": a.status,
                }
                for a in overdue_actions
            ]
            st.table(data_actions)
        else:
            st.info("No overdue leadership actions.")

        # Recently updated initiatives (latest 5 updates)
        recent_updates = (
            session.query(models.InitiativeUpdate)
            .order_by(models.InitiativeUpdate.update_date.desc())
            .limit(5)
            .all()
        )
        if recent_updates:
            st.subheader("Recent Initiative Updates")
            data_updates = [
                {
                    "Initiative": u.initiative.code,
                    "Date": u.update_date,
                    "Progress %": u.progress_pct,
                    "Status": u.status,
                    "Author": u.author.full_name,
                }
                for u in recent_updates
            ]
            st.table(data_updates)
        else:
            st.info("No recent updates.")

        # Department performance summary (table)
        st.subheader("Department Performance Summary")
        summary_rows = []
        for r in dept_rates:
            summary_rows.append(
                {
                    "Department": r["department"],
                    "Total Initiatives": r["total_initiatives"],
                    "Completed Initiatives": r["completed_initiatives"],
                    "Completion %": (
                        f'{r["completion_pct"]:.1f}%' if r["completion_pct"] is not None else "—"
                    ),
                }
            )
        st.table(summary_rows)

if __name__ == "__main__":
    main()
