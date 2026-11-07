import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="department")
    initiatives: Mapped[List["Initiative"]] = relationship("Initiative", back_populates="department")
    kpi_definitions: Mapped[List["KPIDefinition"]] = relationship("KPIDefinition", back_populates="department")
    kpi_measurements: Mapped[List["KPIMeasurement"]] = relationship("KPIMeasurement", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="employees")
    initiatives: Mapped[List["Initiative"]] = relationship("Initiative", back_populates="owner")
    milestones: Mapped[List["Milestone"]] = relationship("Milestone", back_populates="owner")
    initiative_updates: Mapped[List["InitiativeUpdate"]] = relationship("InitiativeUpdate", back_populates="author")
    leadership_actions: Mapped[List["LeadershipAction"]] = relationship("LeadershipAction", back_populates="owner")


class InitiativeDependency(Base):
    __tablename__ = "initiative_dependencies"

    initiative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="CASCADE"), primary_key=True
    )
    depends_on_initiative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="RESTRICT"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("initiative_id != depends_on_initiative_id", name="check_no_self_dependency"),
    )


class Initiative(Base):
    __tablename__ = "initiatives"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strategic_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Not Started")
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("progress_pct >= 0 AND progress_pct <= 100", name="check_initiative_progress_range"),
        CheckConstraint("target_date >= start_date", name="check_initiative_dates"),
        Index("ix_initiatives_dept_status", "department_id", "status"),
        Index("ix_initiatives_owner_id", "owner_id"),
        Index("ix_initiatives_target_date", "target_date"),
    )

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="initiatives")
    owner: Mapped["Employee"] = relationship("Employee", back_populates="initiatives")
    milestones: Mapped[List["Milestone"]] = relationship("Milestone", back_populates="initiative", cascade="all, delete-orphan")
    updates: Mapped[List["InitiativeUpdate"]] = relationship("InitiativeUpdate", back_populates="initiative", cascade="all, delete-orphan")
    risks: Mapped[List["Risk"]] = relationship("Risk", back_populates="initiative", cascade="all, delete-orphan")
    leadership_actions: Mapped[List["LeadershipAction"]] = relationship("LeadershipAction", back_populates="initiative")
    leadership_decisions: Mapped[List["LeadershipDecision"]] = relationship("LeadershipDecision", back_populates="initiative")

    dependencies: Mapped[List["Initiative"]] = relationship(
        "Initiative",
        secondary="initiative_dependencies",
        primaryjoin="Initiative.id == InitiativeDependency.initiative_id",
        secondaryjoin="Initiative.id == InitiativeDependency.depends_on_initiative_id",
        backref="dependent_initiatives",
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Not Started")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(status != 'Completed') OR (actual_date IS NOT NULL)",
            name="check_milestone_completed_actual_date"
        ),
        Index("ix_milestones_init_planned_status", "initiative_id", "planned_date", "status"),
    )

    initiative: Mapped["Initiative"] = relationship("Initiative", back_populates="milestones")
    owner: Mapped["Employee"] = relationship("Employee", back_populates="milestones")


class InitiativeUpdate(Base):
    __tablename__ = "initiative_updates"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    update_date: Mapped[date] = mapped_column(Date, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    update_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("progress_pct >= 0 AND progress_pct <= 100", name="check_update_progress_range"),
        Index("ix_initiative_updates_init_date", "initiative_id", "update_date"),
    )

    initiative: Mapped["Initiative"] = relationship("Initiative", back_populates="updates")
    author: Mapped["Employee"] = relationship("Employee", back_populates="initiative_updates")


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g., Low, Medium, High, Critical
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Open")  # e.g., Open, Mitigated, Closed
    identified_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    initiative: Mapped["Initiative"] = relationship("Initiative", back_populates="risks")


class ManagementMeeting(Base):
    __tablename__ = "management_meetings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    meeting_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Executive Review")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    actions: Mapped[List["LeadershipAction"]] = relationship("LeadershipAction", back_populates="meeting")
    decisions: Mapped[List["LeadershipDecision"]] = relationship("LeadershipDecision", back_populates="meeting")


class LeadershipAction(Base):
    __tablename__ = "leadership_actions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("management_meetings.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="Medium")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Open")
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_leadership_actions_owner_deadline_status", "owner_id", "deadline", "status"),
    )

    initiative: Mapped[Optional["Initiative"]] = relationship("Initiative", back_populates="leadership_actions")
    owner: Mapped["Employee"] = relationship("Employee", back_populates="leadership_actions")
    meeting: Mapped[Optional["ManagementMeeting"]] = relationship("ManagementMeeting", back_populates="actions")


class LeadershipDecision(Base):
    __tablename__ = "leadership_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    initiative_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("initiatives.id", ondelete="SET NULL"), nullable=True
    )
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("management_meetings.id", ondelete="SET NULL"), nullable=True
    )
    decision_text: Mapped[str] = mapped_column(Text, nullable=False)
    decision_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="Pending")
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_leadership_decisions_status_date", "status", "decision_date"),
    )

    initiative: Mapped[Optional["Initiative"]] = relationship("Initiative", back_populates="leadership_decisions")
    meeting: Mapped[Optional["ManagementMeeting"]] = relationship("ManagementMeeting", back_populates="decisions")


class KPIDefinition(Base):
    __tablename__ = "kpi_definitions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="Higher is better")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="kpi_definitions")
    measurements: Mapped[List["KPIMeasurement"]] = relationship("KPIMeasurement", back_populates="definition", cascade="all, delete-orphan")


class KPIMeasurement(Base):
    __tablename__ = "kpi_measurements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    definition_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("kpi_definitions.id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_kpi_meas_def_date_dept", "definition_id", "measurement_date", "department_id"),
    )

    definition: Mapped["KPIDefinition"] = relationship("KPIDefinition", back_populates="measurements")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="kpi_measurements")
