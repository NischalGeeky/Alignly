# Alignly: Business Operations & Executive Intelligence Platform

> **A practical operations command center for tracking strategic
> execution, surfacing delivery risks, maintaining leadership
> accountability, and preparing management reviews.**

Alignly consolidates initiative, milestone, KPI, risk, decision, and
action data into one management interface. It is designed for a
fictional mid-sized organization and uses transparent business rules to
identify execution exceptions. It is not intended to replace an
organization's ERP, HRIS, project-management system, or formal
business-intelligence platform.

**Product tagline:** Bringing strategy, teams, and execution into
alignment.\
**Project type:** Portfolio-ready business operations application\
**Primary users:** Chief of Staff, Business Operations, Department
Heads, Initiative Owners\
**Initial delivery target:** Working local MVP in 2--3 focused
development days; additional time for validation, polish, and optional
AI/automation\
**Recommended implementation:** Python 3.11+, Streamlit, SQLAlchemy,
PostgreSQL/Supabase, Pandas, Plotly

------------------------------------------------------------------------

## Table of contents

-   [1. Problem and product rationale](#1-problem-and-product-rationale)
-   [2. Product objectives and
    non-goals](#2-product-objectives-and-non-goals)
-   [3. Users and core workflows](#3-users-and-core-workflows)
-   [4. Scope and feature
    requirements](#4-scope-and-feature-requirements)
-   [5. Technology decisions](#5-technology-decisions)
-   [6. System architecture](#6-system-architecture)
-   [7. Data model and database
    design](#7-data-model-and-database-design)
-   [8. KPI definitions and calculation
    rules](#8-kpi-definitions-and-calculation-rules)
-   [9. Risk and execution
    intelligence](#9-risk-and-execution-intelligence)
-   [10. Application structure](#10-application-structure)
-   [11. UI and interaction
    requirements](#11-ui-and-interaction-requirements)
-   [12. Data import and export](#12-data-import-and-export)
-   [13. AI reporting design](#13-ai-reporting-design)
-   [14. Optional n8n automation](#14-optional-n8n-automation)
-   [15. Security, reliability, and
    auditability](#15-security-reliability-and-auditability)
-   [16. Installation and local setup](#16-installation-and-local-setup)
-   [17. Database initialization and sample
    data](#17-database-initialization-and-sample-data)
-   [18. Running the application](#18-running-the-application)
-   [19. Testing strategy](#19-testing-strategy)
-   [20. Implementation roadmap](#20-implementation-roadmap)
-   [21. MVP acceptance checklist](#21-mvp-acceptance-checklist)
-   [22. Fictional demonstration
    scenario](#22-fictional-demonstration-scenario)
-   [23. Deployment guide](#23-deployment-guide)
-   [24. Screenshots](#24-screenshots)
-   [25. Limitations and assumptions](#25-limitations-and-assumptions)
-   [26. Future enhancements](#26-future-enhancements)
-   [27. Learning outcomes](#27-learning-outcomes)

------------------------------------------------------------------------

## 1. Problem and product rationale

### The problem

Operational information is commonly distributed across spreadsheets,
email threads, meeting notes, slide decks, and separate project tools.
Leadership may receive status updates, but still struggle to answer
operationally important questions consistently:

-   Which strategic initiatives are genuinely on track?
-   Which commitments have slipped, and by how much?
-   Which departments have a concentration of overdue work?
-   Which dependencies or decisions are preventing execution?
-   Which owners need support or escalation?
-   What should be discussed at the next management review?

A status dashboard alone does not solve this problem. Leaders need
traceability from an exception to its underlying initiative, milestone,
owner, decision, and next action.

### Product response

Alignly provides a lightweight operational control layer. It combines
structured records with deterministic calculations and a concise
exception workflow:

1.  Capture initiatives, milestones, updates, KPIs, risks, decisions,
    and actions.
2.  Calculate progress and operational metrics from stored records.
3.  Apply explicit rules to identify execution exceptions.
4.  Route each exception to a recommended next step and accountable
    owner.
5.  Assemble management-review material from the same verified dataset.
6.  Optionally use an LLM to turn verified facts into readable executive
    commentary.

### Product principle

**Facts are calculated by application logic; AI may explain those facts,
but must not create them.**

Every number shown in a report must be traceable to a database query or
deterministic calculation. AI-generated recommendations must be labelled
as recommendations, not reported as completed actions or verified facts.

------------------------------------------------------------------------

## 2. Product objectives and non-goals

### Objectives

  ---------------------------------------------------------------------
  Objective                          Product outcome
  ---------------------------------- ----------------------------------
  Create one operational view        Shared view of initiatives,
                                     departments, milestones,
                                     decisions, and actions

  Improve execution visibility       Exceptions are identified using
                                     consistent, documented rules

  Strengthen accountability          Each initiative, milestone, and
                                     action has an owner

  Improve management cadence         Weekly summaries and meeting
                                     agendas can be generated from
                                     current data

  Support evidence-based decisions   KPIs and risk indicators expose
                                     their calculation logic

  Reduce manual reporting effort     Filtered Excel exports and
                                     structured PDF reports
  ---------------------------------------------------------------------

### Non-goals for the initial release

-   Full project scheduling, Gantt dependency management, or resource
    capacity planning.
-   Replacing Jira, Asana, Monday.com, ERP, HRIS, CRM, or a data
    warehouse.
-   Real-time integrations with enterprise systems.
-   Statistical or machine-learning prediction of project failure.
-   Multi-tenant SaaS billing, SSO, enterprise identity management, or
    granular production RBAC.
-   Sending real company-confidential data to an external AI provider by
    default.

Keep these boundaries visible in the UI and documentation. The project
is an operational intelligence prototype, not a production-certified
enterprise platform.

------------------------------------------------------------------------

## 3. Users and core workflows

  -----------------------------------------------------------------------
  User                    Primary need            Typical activity
  ----------------------- ----------------------- -----------------------
  Chief of Staff /        Organization-wide       Review exceptions,
  Business Operations     execution visibility    decisions, and
                                                  management priorities

  Department Head         Department delivery     Review initiatives,
                          performance             overdue milestones, and
                                                  owner accountability

  Initiative Owner        Clear commitments and   Update progress,
                          status                  milestones,
                                                  dependencies, and
                                                  blockers

  Executive / Leadership  Concise decision-ready  Review a summary,
                          information             resolve pending
                                                  decisions, assign
                                                  actions
  -----------------------------------------------------------------------

### Core workflow: weekly operating cadence

1.  Initiative owners update progress and add a dated status update.
2.  Department heads review upcoming and overdue milestones.
3.  Alignly recalculates KPIs and execution risk when pages load or data
    changes.
4.  Business Operations reviews the exception queue and validates
    unusual flags.
5.  The Chief of Staff prepares the weekly summary and management
    agenda.
6.  Leadership decisions are recorded as decisions and/or actions with
    owners and due dates.
7.  The next review checks whether those actions were closed.

A status change does not automatically mean an initiative is healthy.
Risk is calculated independently from the initiative's status so that,
for example, an initiative marked `In Progress` can still be flagged as
high risk.

------------------------------------------------------------------------

## 4. Scope and feature requirements

The application has six modules. The MVP includes the first five
operational capabilities and a usable meeting-preparation workflow; AI
narrative generation is a post-MVP enhancement.

### Module 1 --- Executive Command Center

**Purpose:** Give leadership a concise, filterable view of
organizational execution.

KPI cards:

-   Total strategic initiatives
-   Completed initiatives
-   In-progress initiatives
-   At-risk and blocked initiatives
-   Overdue initiatives
-   Initiative completion rate
-   Open leadership actions
-   Pending leadership decisions

Charts:

-   Initiative status distribution
-   Department completion rate
-   Initiative progress by month (based on dated updates where
    available)
-   Risk classification distribution
-   Overdue milestone count by department

Filters: department, reporting date/period, priority, and status.

**Rules** - All cards and charts must respond to the same active filters
unless a chart is explicitly labelled as organization-wide. - Empty
datasets must show a useful empty state, not a fabricated
zero-performance narrative. - Display the reporting date and clarify
whether a value is a count, percentage, or score. - A click on an
exception count should navigate to the corresponding filtered list where
practical.

### Module 2 --- Strategic Initiative and Milestone Tracker

Each initiative contains:

  ---------------------------------------------------------------------
  Field                              Type / rule
  ---------------------------------- ----------------------------------
  Initiative ID                      UUID primary key; human-readable
                                     code such as `INI-0001` shown in
                                     UI

  Name                               Required, max 200 characters

  Description                        Optional text

  Department                         Required foreign key

  Owner                              Required employee foreign key

  Priority                           `Low`, `Medium`, `High`,
                                     `Critical`

  Start date                         Required date

  Target completion date             Required date; must be on/after
                                     start date

  Status                             `Not Started`, `In Progress`,
                                     `At Risk`, `Blocked`, `Completed`

  Progress                           Integer 0--100

  Strategic objective                Optional text

  Expected outcome                   Optional text

  Dependencies                       Captured through initiative
                                     dependency relationships

  Latest update                      Derived from most recent
                                     initiative update; do not
                                     duplicate as the source of truth

  Last updated                       Database timestamp
  ---------------------------------------------------------------------

Each milestone contains an ID, initiative, name, owner, planned date,
actual completion date, status, and notes. Milestone statuses:
`Not Started`, `In Progress`, `Completed`, `Blocked`.

**Business rules** - A completed milestone requires an actual completion
date. - A completed initiative must have 100% progress. The service
layer should either enforce this on transition or reject inconsistent
updates with a clear message. - An initiative cannot be marked completed
while required milestones remain incomplete unless an explicit override
is implemented and recorded. For the MVP, reject the transition and
explain why. - Progress is manually maintained at initiative level in
the MVP. Do not silently derive it from milestone counts because
milestones may have different weights. A future weighted-progress
feature can be added explicitly. - Record each update in
`initiative_updates`; do not overwrite the history with only a
latest-update text field.

### Module 3 --- Risk and Execution Intelligence

A deterministic rules engine flags:

1.  Overdue incomplete milestones.
2.  Initiatives without an update in more than seven days.
3.  Initiatives with blocked dependencies.
4.  Actual progress materially below expected progress.
5.  High/critical priority initiatives approaching their target date.
6.  Repeatedly delayed milestones (for the MVP, a milestone is
    considered repeatedly delayed if its planned date has been revised
    at least twice; if date revision history is not implemented, omit
    this rule rather than infer it).

For each exception show initiative, department, owner, issue, score,
classification, recommended action, and escalation priority. The rules
and thresholds are described in [Risk and execution
intelligence](#9-risk-and-execution-intelligence).

### Module 4 --- Leadership Decision and Action Tracker

Actions record the work required after a meeting or decision:

-   Action ID, related initiative (optional), description,
    meeting/decision date, owner, deadline, priority, status, completion
    date, and comments.
-   Statuses: `Open`, `In Progress`, `Pending Approval`, `Completed`,
    `Overdue`.

`Overdue` is a derived operational state when an incomplete action's
deadline has passed. It may be displayed as a status, but the stored
workflow status should remain one of `Open`, `In Progress`, or
`Pending Approval`. This avoids needing a scheduled job to keep stored
status synchronized with the calendar.

Decision records capture the decision statement, decision date, decision
owner/meeting, related initiative, rationale, and follow-up action if
applicable. A pending decision is a decision record with status
`Pending`; approved/rejected decisions should retain their history.

### Module 5 --- AI-Powered Executive Reporting

Post-MVP integration with Gemini generates: - Weekly executive summary -
Department performance narrative - Management attention report (up to
five high-priority exceptions) - Management-review briefing

The application calculates and packages the facts first. The AI receives
a compact, structured payload and returns narrative only. See [AI
reporting design](#13-ai-reporting-design).

### Module 6 --- Management Review Preparation

Generate a review pack containing: 1. Review of previous action items.
2. Strategic initiative updates. 3. Department performance. 4. Execution
risks and bottlenecks. 5. Pending leadership decisions. 6. Next steps
and accountability.

The agenda is generated from database records and can be edited before
export. Include owner and due date beside each action. Export to PDF in
the MVP. PowerPoint export is optional and should not delay the core
release.

------------------------------------------------------------------------

## 5. Technology decisions

  -----------------------------------------------------------------------
  Layer                   Selected technology     Reason
  ----------------------- ----------------------- -----------------------
  Language                Python 3.11+            Familiar, productive,
                                                  broad data ecosystem

  UI/application          Streamlit               Fast multi-page
                                                  internal-tool interface

  Data manipulation       Pandas                  CSV/Excel validation
                                                  and tabular
                                                  transformations

  ORM                     SQLAlchemy 2.x          Parameterized database
                                                  access and relational
                                                  models

  Primary database        PostgreSQL              Relational integrity
                                                  and hosted deployment
                                                  support

  Hosted PostgreSQL       Supabase                Managed PostgreSQL with
                                                  simple project
                                                  provisioning

  Local fallback          SQLite                  Low-friction local
                                                  development and tests

  Charts                  Plotly                  Interactive business
                                                  charts

  Excel                   OpenPyXL                Workbook generation and
                                                  template formatting

  PDF                     ReportLab               Programmatic PDF
                                                  reports

  AI                      Google Gemini API       Executive narrative
                          (optional)              generation

  Automation              n8n (optional)          Scheduled reminders and
                                                  report delivery

  Testing                 pytest                  Unit and service-level
                                                  tests

  Version control         Git/GitHub              Change history and
                                                  collaboration

  Hosting                 Streamlit Community     Simple demonstration
                          Cloud                   deployment
  -----------------------------------------------------------------------

### Dependency policy

-   Pin compatible major versions in `requirements.txt`; update
    intentionally.
-   Do not introduce FastAPI, React, Celery, Redis, microservices, or
    Docker for the MVP.
-   Use one Streamlit process and one relational database.
-   Keep Gemini and n8n optional. The core application must work with
    both disabled.
-   Use SQLAlchemy sessions and service functions; do not place SQL or
    business rules directly in page files.

------------------------------------------------------------------------

## 6. System architecture

### Logical architecture

``` mermaid
flowchart TB
    U[Business Operations / Leadership User] --> UI[Streamlit Multi-page UI]
    UI --> S[Application Service Layer]
    S --> KPI[KPI and Reporting Services]
    S --> RISK[Rule-based Risk Engine]
    S --> CRUD[Initiative, Milestone, Action Services]
    CRUD --> ORM[SQLAlchemy ORM]
    KPI --> ORM
    RISK --> ORM
    ORM --> DB[(PostgreSQL / Supabase)]
    ORM -. local development .-> SQLITE[(SQLite)]
    KPI --> EXPORT[Excel / PDF Exporters]
    REPORT[Verified Report Payload] --> AI{Gemini enabled?}
    AI -->|Yes| GEM[Gemini API]
    AI -->|No / error| FALLBACK[Deterministic Template]
    GEM --> NARRATIVE[Executive Narrative]
    FALLBACK --> NARRATIVE
    N8N[n8n - optional] -. scheduled API or webhook integration .-> S
```

### Request/data flow

1.  Streamlit page collects input and validates basic form fields.
2.  Page calls a service function; it does not write directly to the
    database.
3.  Service applies business rules and commits a transaction.
4.  SQLAlchemy persists records in PostgreSQL/SQLite.
5.  KPI and risk services query current records and return structured
    results.
6.  UI renders tables, cards, and Plotly charts.
7.  Export services use the same filtered, verified data.
8.  AI reporting, if enabled, receives only the explicitly approved
    report payload.

### Architectural conventions

-   **Pages:** presentation, navigation, input collection, and
    rendering.
-   **Services:** business logic and transaction boundaries.
-   **Models:** relational schema and constraints.
-   **Repositories:** optional thin query helpers; do not create an
    abstraction for every query.
-   **Utils:** validation, date handling, formatting, and export
    helpers.
-   **Tests:** test deterministic services without requiring Streamlit
    UI automation.

### Error handling

Catch expected errors at the page boundary and display actionable
messages. Log technical details with Python's `logging` module; do not
expose stack traces or credentials to users. Database write operations
should use transactions and roll back on failure.

------------------------------------------------------------------------

## 7. Data model and database design

### Entity relationship diagram

``` mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : contains
    DEPARTMENTS ||--o{ INITIATIVES : owns
    EMPLOYEES ||--o{ INITIATIVES : leads
    INITIATIVES ||--o{ MILESTONES : contains
    EMPLOYEES ||--o{ MILESTONES : owns
    INITIATIVES ||--o{ INITIATIVE_UPDATES : records
    EMPLOYEES ||--o{ INITIATIVE_UPDATES : authors
    INITIATIVES ||--o{ RISKS : has
    INITIATIVES ||--o{ LEADERSHIP_ACTIONS : relates_to
    EMPLOYEES ||--o{ LEADERSHIP_ACTIONS : owns
    INITIATIVES ||--o{ LEADERSHIP_DECISIONS : relates_to
    MANAGEMENT_MEETINGS ||--o{ LEADERSHIP_DECISIONS : records
    MANAGEMENT_MEETINGS ||--o{ LEADERSHIP_ACTIONS : creates
    DEPARTMENTS ||--o{ KPI_DEFINITIONS : scopes
    KPI_DEFINITIONS ||--o{ KPI_MEASUREMENTS : measures
    DEPARTMENTS ||--o{ KPI_MEASUREMENTS : reports

    DEPARTMENTS {
      uuid id PK
      string name UK
      string description
    }
    EMPLOYEES {
      uuid id PK
      uuid department_id FK
      string full_name
      string email UK
      boolean is_active
    }
    INITIATIVES {
      uuid id PK
      string code UK
      uuid department_id FK
      uuid owner_id FK
      string name
      string priority
      date start_date
      date target_date
      string status
      integer progress_pct
    }
    MILESTONES {
      uuid id PK
      uuid initiative_id FK
      uuid owner_id FK
      string name
      date planned_date
      date actual_date
      string status
    }
    INITIATIVE_UPDATES {
      uuid id PK
      uuid initiative_id FK
      uuid author_id FK
      date update_date
      integer progress_pct
      string status
      text update_text
    }
    RISKS {
      uuid id PK
      uuid initiative_id FK
      string title
      text description
      string severity
      string status
      date identified_date
    }
    LEADERSHIP_ACTIONS {
      uuid id PK
      uuid initiative_id FK
      uuid owner_id FK
      uuid meeting_id FK
      text description
      date deadline
      string priority
      string status
      date completed_date
    }
    LEADERSHIP_DECISIONS {
      uuid id PK
      uuid initiative_id FK
      uuid meeting_id FK
      text decision_text
      date decision_date
      string status
      text rationale
    }
    KPI_DEFINITIONS {
      uuid id PK
      uuid department_id FK
      string name
      string unit
      string direction
      boolean is_active
    }
    KPI_MEASUREMENTS {
      uuid id PK
      uuid definition_id FK
      uuid department_id FK
      date measurement_date
      float actual_value
      float target_value
    }
    MANAGEMENT_MEETINGS {
      uuid id PK
      string title
      date meeting_date
      string meeting_type
      string status
    }
```

### Table specification

  ----------------------------------------------------------------------
  Table                    Purpose                Important constraints
  ------------------------ ---------------------- ----------------------
  `departments`            Organizational units   Unique, non-empty name

  `employees`              Demo owners and        Unique email;
                           contributors           department FK

  `initiatives`            Strategic work         Unique code; valid
                           portfolio              dates; progress 0--100

  `milestones`             Initiative             Initiative and owner
                           deliverables           FKs; actual date
                                                  required when
                                                  completed

  `initiative_updates`     Dated status history   Initiative FK; author
                                                  FK; progress 0--100

  `risks`                  Manually recorded      Initiative FK;
                           risks                  severity and status
                                                  constrained

  `leadership_actions`     Accountable follow-up  Owner FK; optional
                           work                   initiative and meeting
                                                  FKs

  `leadership_decisions`   Decision log           Optional initiative
                                                  and meeting FKs;
                                                  decision status
                                                  constrained

  `kpi_definitions`        KPI metadata           Name, unit, direction,
                                                  optional department
                                                  scope

  `kpi_measurements`       Dated actual/target    Definition and
                           values                 department FKs;
                                                  numeric values

  `management_meetings`    Management review      Required title and
                           schedule/history       date
  ----------------------------------------------------------------------

### Recommended SQLAlchemy model conventions

Use SQLAlchemy 2.x typed declarative mappings:

-   UUID primary keys (`Uuid` type) for portable PostgreSQL/SQLite
    behavior.
-   `String` with explicit maximum lengths for codes, names, statuses,
    and emails.
-   `Text` for descriptions, notes, rationales, and update text.
-   `Date` for business dates; `DateTime(timezone=True)` for audit
    timestamps.
-   `Boolean` for active flags.
-   `Numeric` or `Float` for KPI values; use `Numeric` where exact
    decimal precision matters.
-   `CheckConstraint` for progress range and valid numeric ranges.
-   `UniqueConstraint` for department name, employee email, and
    initiative code.
-   `ForeignKey(..., ondelete="RESTRICT")` for core business records to
    prevent accidental deletion of referenced history. Use soft
    deactivation for employees/departments instead of deleting records.
-   Add `created_at` and `updated_at` timestamps to mutable business
    entities.

### Indexes

Create indexes on: - `initiatives(department_id, status)` -
`initiatives(owner_id)` - `initiatives(target_date)` -
`milestones(initiative_id, planned_date, status)` -
`leadership_actions(owner_id, deadline, status)` -
`leadership_decisions(status, decision_date)` -
`initiative_updates(initiative_id, update_date)` -
`kpi_measurements(definition_id, measurement_date, department_id)`

Avoid premature indexing beyond common filters and joins.

### Initiative dependencies

Represent dependencies in a separate association table,
`initiative_dependencies`, rather than storing a comma-separated list.
Fields: `initiative_id`, `depends_on_initiative_id`, `created_at`;
composite primary key; both IDs reference initiatives; disallow
self-dependency. This is an additional table beyond the requested core
eleven and is necessary to query blocked dependencies reliably.

### Database initialization

Create tables from SQLAlchemy metadata for the prototype. For later
schema evolution, introduce Alembic migrations before multiple deployed
versions or production data are used. Do not rely on `create_all()` to
modify existing tables.

------------------------------------------------------------------------

## 8. KPI definitions and calculation rules

All KPI functions accept an explicit `as_of_date` and optional filters.
This makes calculations reproducible in tests and historical reporting.

  -------------------------------------------------------------------------
  Metric                Formula                       Notes
  --------------------- ----------------------------- ---------------------
  Initiative completion Completed initiatives / total `0` when denominator
  rate                  initiatives × 100             is zero; UI should
                                                      label as no data

  Milestone completion  Completed milestones / total  Count milestone
  rate                  milestones × 100              records in selected
                                                      scope

  Overdue milestone     Incomplete milestones with    Completed milestones
  count                 `planned_date < as_of_date`   are never overdue

  Action closure rate   Completed actions / total     Derived overdue state
                        actions × 100                 does not count as
                                                      completed

  Department completion Completed department          Calculated
  rate                  initiatives / department      independently per
                        initiatives × 100             department

  Progress variance     Actual progress − expected    Percentage-point
                        progress                      difference
  -------------------------------------------------------------------------

### Expected progress

For an initiative with start date `S`, target date `T`, and reporting
date `D`:

-   If status is `Completed`, expected progress is 100%.
-   If `D <= S`, expected progress is 0%.
-   If `D >= T`, expected progress is 100% for comparison purposes.
-   Otherwise:

\[ ExpectedProgress = `\frac{D-S}{T-S}`{=tex} `\times 100`{=tex} \]

Clamp the result to `[0, 100]` and round only for display. Keep full
precision for comparisons.

**Progress variance** is:

\[ ProgressVariance = ActualProgress - ExpectedProgress \]

A variance of `-18` means actual progress is 18 percentage points below
the time-based expected progress. This is a planning heuristic, not
proof that delivery will be late.

### Edge cases and interpretation

-   If `target_date == start_date`, expected progress is 0% on/before
    the start date and 100% after it; validate whether same-day
    initiatives are allowed. Recommended MVP rule: allow same-day only
    if a one-day task is intended, and explicitly handle it to avoid
    division by zero.
-   Future initiatives have expected progress 0%.
-   Completed initiatives have expected progress 100%, even if their
    target date is in the future.
-   Cancelled initiatives are not in the MVP status set. If added later,
    exclude them from completion denominators and document the policy.
-   If there are no initiatives or milestones, show `—` / "No records"
    rather than implying 0% performance.
-   All date comparisons use the configured business timezone. Store
    timestamps in UTC and convert for display.
-   Department metrics must use the same reporting date and filters as
    the organization-level metrics.

### KPI definitions versus initiative metrics

`kpi_definitions` and `kpi_measurements` support operational KPIs such
as customer response time, order accuracy, or process cycle time.
Initiative completion and milestone metrics are calculated from the
initiative domain tables and should not be duplicated as manually
entered KPI measurements.

------------------------------------------------------------------------

## 9. Risk and execution intelligence

### Risk scoring model

The MVP uses a transparent, configurable heuristic. It is **not** a
statistically trained predictive model and must not be described as one.

For each initiative, evaluate the following signals as of the reporting
date:

  ---------------------------------------------------------------------
  Signal                                    Points Trigger
  -------------------- --------------------------- --------------------
  Overdue milestone                             30 At least one
                                                   incomplete milestone
                                                   has planned date
                                                   before `as_of_date`

  Progress                                      25 Progress variance is
  significantly behind                             -15 percentage
                                                   points or lower

  Blocked dependency                            20 At least one
                                                   prerequisite
                                                   initiative is
                                                   `Blocked`

  Stale update                                  15 Most recent update
                                                   is more than 7
                                                   calendar days old

  High-priority                                 10 Priority is
  deadline approaching                             High/Critical and
                                                   target date is
                                                   within the next 14
                                                   days
  ---------------------------------------------------------------------

Raw score is the sum of applicable points, capped at 100. Since the
listed maximum is 100, capping is defensive. Each signal contributes at
most once per initiative in the MVP; multiple overdue milestones do not
multiply the 30-point signal.

Classification:

      Score Classification
  --------- ----------------
      0--29 Low
     30--59 Medium
     60--79 High
    80--100 Critical

### Recommended action mapping

  ---------------------------------------------------------------------
  Trigger                            Recommended action
  ---------------------------------- ----------------------------------
  Overdue milestone                  Confirm revised delivery date with
                                     owner; document recovery plan

  Progress significantly behind      Request milestone-level recovery
                                     plan and review scope/resources

  Blocked dependency                 Escalate to the prerequisite
                                     initiative owner; agree unblock
                                     date

  Stale update                       Request a current status update
                                     from the initiative owner

  High-priority deadline approaching Confirm readiness, outstanding
                                     dependencies, and executive
                                     support required
  ---------------------------------------------------------------------

If several signals apply, display all identified issues and choose the
highest escalation priority based on the overall classification. Do not
imply that a single recommendation resolves every issue.

### Exception report fields

`initiative_code`, `initiative_name`, `department`, `owner`,
`identified_issues[]`, `risk_score`, `risk_classification`,
`recommended_actions[]`, `escalation_priority`, `as_of_date`.

### Important implementation details

-   Use a pure function such as
    `calculate_initiative_risk(initiative, milestones, dependencies, latest_update, as_of_date, config)`.
-   Keep thresholds in a configuration object, not scattered through
    page code.
-   Return both score and triggered reasons so that users can understand
    why an initiative was flagged.
-   Do not count an initiative's own blocked status as a blocked
    *dependency* signal; those are separate conditions.
-   A missing update history should be treated as stale if the
    initiative is old enough to require an update; document this rule.
-   A target date in the past is not the same as an approaching
    deadline. Overdue milestones and progress variance handle delivery
    slippage; add an explicit overdue-initiative signal only if the
    scoring policy is revised and documented.
-   Risk score is a prioritization aid. It is not a probability of
    failure.

------------------------------------------------------------------------

## 10. Application structure

Recommended repository layout:

``` text
alignly/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── pages/
│   ├── 1_Executive_Command_Center.py
│   ├── 2_Initiative_Tracker.py
│   ├── 3_Risk_Intelligence.py
│   ├── 4_Leadership_Actions.py
│   ├── 5_Executive_Reports.py
│   └── 6_Management_Reviews.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── models.py
│   ├── seed_data.py
│   └── queries.py
├── services/
│   ├── __init__.py
│   ├── initiative_service.py
│   ├── milestone_service.py
│   ├── action_service.py
│   ├── decision_service.py
│   ├── kpi_service.py
│   ├── risk_engine.py
│   ├── reporting_service.py
│   └── ai_service.py
├── utils/
│   ├── validators.py
│   ├── date_utils.py
│   ├── exporters.py
│   ├── formatting.py
│   └── logging_config.py
├── sample_data/
│   ├── departments.csv
│   ├── employees.csv
│   ├── initiatives.csv
│   ├── milestones.csv
│   ├── initiative_updates.csv
│   ├── initiative_dependencies.csv
│   ├── leadership_actions.csv
│   └── leadership_decisions.csv
├── tests/
│   ├── conftest.py
│   ├── test_kpi_calculations.py
│   ├── test_risk_engine.py
│   ├── test_initiative_rules.py
│   ├── test_data_validation.py
│   ├── test_import_export.py
│   └── test_ai_fallback.py
└── assets/
    ├── logo.png
    └── screenshots/
```

### Module ownership

  ---------------------------------------------------------------------
  File                               Responsibility
  ---------------------------------- ----------------------------------
  `app.py`                           App title, global configuration,
                                     navigation landing

  `config.py`                        Environment configuration and
                                     constants

  `database/connection.py`           Engine, session factory, session
                                     context manager

  `database/models.py`               SQLAlchemy models and constraints

  `database/seed_data.py`            Idempotent demo-data seeding

  `services/*`                       Business rules and
                                     transaction-safe operations

  `utils/validators.py`              CSV/Excel schema and field
                                     validation

  `utils/exporters.py`               Excel and PDF generation

  `pages/*`                          Streamlit presentation layer

  `tests/*`                          Deterministic automated tests
  ---------------------------------------------------------------------

Keep page files short. A page should call service functions and render
their returned data; it should not contain the risk algorithm or KPI
formulas.

------------------------------------------------------------------------

## 11. UI and interaction requirements

### Navigation

Use Streamlit's native multipage navigation or `pages/` convention.
Sidebar order:

1.  Executive Command Center
2.  Initiative Tracker
3.  Risk Intelligence
4.  Leadership Actions
5.  Executive Reports
6.  Management Reviews

### Visual language

-   Restrained corporate palette: navy/charcoal, neutral backgrounds,
    and one accent color.
-   Use status colors consistently: green for completed/low risk, amber
    for medium/at risk, red for high/critical/overdue, grey for not
    started.
-   Do not use color as the only status indicator; include text labels.
-   Use consistent date formats and percentage precision.
-   Prefer compact charts with a clear title, unit, and reporting
    period.
-   Avoid decorative gradients, excessive animation, and charts that do
    not support a decision.

### Required interactions

-   Search initiatives by name/code.
-   Filter initiative list by department, owner, priority, status, and
    due-date range.
-   View initiative detail including milestones, dependencies, updates,
    and calculated risk.
-   Add a dated initiative update.
-   Add/edit milestone and leadership action.
-   Record a leadership decision and its follow-up.
-   Filter exception report by risk level, department, and owner.
-   Export the currently filtered view.
-   Confirm destructive or irreversible actions; prefer
    archive/deactivate over delete.

### Empty and error states

Every module must handle: - No records yet. - No records match current
filters. - Missing optional data. - Database unavailable. - Invalid user
input. - Export failure.

Display a clear next step (for example, "No initiatives found. Add an
initiative or clear filters."). Do not fabricate sample values when the
database is empty; sample data should be seeded explicitly.

------------------------------------------------------------------------

## 12. Data import and export

### Supported imports

MVP import targets: initiatives, milestones, and leadership actions.
Departments and employees should be seeded or created through controlled
admin/demo setup so that imported records can resolve foreign keys.

Provide a downloadable Excel template with: - One sheet per supported
entity. - Required columns clearly marked. - Example rows labelled as
examples. - Allowed status and priority values documented in a `Read Me`
sheet.

### Import pipeline

1.  Read workbook using Pandas/OpenPyXL.
2.  Normalize column names (trim whitespace; case-insensitive matching).
3.  Validate required columns.
4.  Validate data types, dates, enums, progress ranges, and foreign-key
    references.
5.  Detect duplicates using stable business keys (`code` for
    initiatives; a documented composite key for milestones/actions).
6.  Show a preview with accepted and rejected row counts and row-level
    error messages.
7.  Require explicit confirmation before committing accepted rows.
8.  Commit in a transaction; roll back the batch on database failure.

Do not silently skip invalid rows. The UI must let users download a
validation-error workbook or view row-level errors.

### Export behavior

-   Excel: export current filtered rows, with readable column names,
    frozen header row, filters, sensible widths, and a generated-at
    timestamp.
-   PDF: include title, reporting period, key metrics, exception
    summary, pending decisions, and source-data timestamp.
-   Export only the records in the active filter scope and state that
    scope in the report.
-   Use ReportLab for PDF layout. Keep tables readable and split long
    tables across pages.

------------------------------------------------------------------------

## 13. AI reporting design

### Data contract

The application should create a verified payload before calling Gemini.
Example:

``` json
{
  "report_type": "weekly_executive_summary",
  "reporting_period": {
    "start": "2026-10-26",
    "end": "2026-11-01"
  },
  "generated_at": "2026-11-02T09:00:00Z",
  "organization_metrics": {
    "initiative_count": 15,
    "completed_count": 3,
    "completion_rate_pct": 20.0,
    "overdue_milestone_count": 4,
    "open_action_count": 6,
    "pending_decision_count": 2
  },
  "exceptions": [
    {
      "initiative_code": "INI-0007",
      "department": "Customer Operations",
      "owner": "Demo Owner",
      "risk_score": 75,
      "risk_classification": "High",
      "issues": ["Overdue milestone", "Progress below expected"]
    }
  ]
}
```

The numbers above are illustrative schema examples, not live product
metrics. Actual values must be generated from the database.

### Prompt requirements

The system prompt must instruct the model to: - Use only supplied
facts. - Never invent metrics, owners, dates, achievements, or status
changes. - Identify missing information explicitly. - Separate "Observed
facts" from "Suggested management actions". - Avoid asserting causality
unless the source data supports it. - Keep the report concise, neutral,
and suitable for leadership. - Include the reporting period and
generated timestamp. - Return structured sections (JSON or validated
headings) that the application can render.

Validate model output before display. If the API times out, returns
invalid output, is not configured, or is unavailable, use a
deterministic template-based report built from the same payload.

### Privacy and configuration

-   Gemini is disabled unless `GEMINI_API_KEY` is configured and the
    user explicitly enables AI reporting.
-   Provide a warning that selected report data will be sent to the
    configured external provider.
-   Do not send free-text confidential notes by default. Prefer
    minimized, structured data.
-   Do not include employee email addresses or other unnecessary
    personal data in the AI payload.
-   Keep API keys in environment variables or Streamlit secrets, never
    in source control.

------------------------------------------------------------------------

## 14. Optional n8n automation

The core application must not depend on n8n.

Potential workflows: - Daily reminder for milestones due in the next
three days. - Owner notification for overdue milestones/actions. -
Weekly report generation and delivery. - Critical-risk notification to a
designated reviewer.

### Integration approach

For a student demonstration, the simplest safe approach is: 1. Add a
read-only export endpoint or scheduled data export only if an API layer
is deliberately introduced. 2. Otherwise use a controlled webhook
trigger that receives a minimal event payload from the application. 3.
Store webhook URL and token as secrets. 4. Log whether a notification
was attempted and whether the webhook responded successfully.

Do not expose the database directly to n8n or place credentials in
workflow screenshots. If n8n is unavailable, show the same reminders in
the in-app exception center.

------------------------------------------------------------------------

## 15. Security, reliability, and auditability

### Required safeguards

-   Load configuration from environment variables or Streamlit secrets.
-   Never commit `.env`, API keys, database passwords, or real company
    data.
-   Use SQLAlchemy ORM/query parameters; never build SQL from untrusted
    string concatenation.
-   Validate all imported and form-submitted data in service functions,
    not only in UI widgets.
-   Use transactions for multi-record writes and imports.
-   Apply restrictive database credentials and TLS for hosted
    PostgreSQL.
-   Log application errors without logging secrets or unnecessary
    personal data.
-   Use synthetic names, emails, initiatives, and metrics in the public
    demo.
-   Provide a visible "Demo data" label when seeded sample data is
    active.

### Demo access control

The MVP is a single-workspace demonstration application. Do not claim
production-grade authentication or role-based access control unless it
is actually implemented and tested. If deployed publicly, protect the
demo using Streamlit-supported access controls or keep the dataset
entirely synthetic. Do not expose a public write-enabled database
without appropriate authentication and authorization.

### Backup and recovery

-   Use Supabase's available backup/export options for hosted data and
    periodically export critical demo data.
-   For SQLite, back up the database file while the application is
    stopped or use SQLite's backup API.
-   Test restoration, not just backup creation.
-   Do not treat CSV exports as a complete database backup because they
    may omit relationships and history.

### Reliability

-   Use connection pooling defaults appropriate to Streamlit's process
    model.
-   Use a session context manager and always close sessions.
-   Set reasonable timeouts for external AI/webhook calls.
-   Make seed operations idempotent so repeated runs do not create
    duplicate demo records.
-   Surface a graceful fallback if the database or optional integrations
    are unavailable.

------------------------------------------------------------------------

## 16. Installation and local setup

### Prerequisites

-   Python 3.11 or newer
-   Git
-   PostgreSQL database (optional for local demo; SQLite fallback is
    supported)
-   Gemini API key only if enabling AI reporting

### Clone and create environment

``` bash
git clone https://github.com/<your-username>/alignly.git
cd alignly

python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Recommended `requirements.txt`

``` text
streamlit
pandas
sqlalchemy>=2.0
psycopg[binary]
plotly
openpyxl
reportlab
python-dotenv
google-genai
pytest
```

Pin tested versions before publishing a stable release. If the Gemini
SDK is not installed or configured, the application must still run with
deterministic reporting fallback. Consider separating optional
dependencies into `requirements-ai.txt` if keeping the core install
minimal is important.

### Environment variables

Create `.env` from `.env.example`:

``` dotenv
# SQLite local fallback:
DATABASE_URL=sqlite:///./alignly.db

# Hosted PostgreSQL example:
# DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require

APP_ENV=development
APP_TIMEZONE=Asia/Kolkata
ENABLE_DEMO_SEED=true

# Optional AI. Disabled unless explicitly enabled.
ENABLE_AI_REPORTING=false
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# Optional n8n integration
ENABLE_N8N=false
N8N_WEBHOOK_URL=
N8N_WEBHOOK_TOKEN=
```

Never commit a populated `.env` file. Commit only `.env.example` with
empty values.

### Configuration rules

-   `DATABASE_URL` is required; default to SQLite only for local
    development.
-   `APP_TIMEZONE` controls display and business-date interpretation.
-   `ENABLE_DEMO_SEED` controls whether demo data is inserted when
    initializing a fresh database.
-   `ENABLE_AI_REPORTING` must default to false.
-   Optional integration failures must not prevent the application from
    starting.

------------------------------------------------------------------------

## 17. Database initialization and sample data

### Initialization commands

Provide a small CLI or module entry point so setup is repeatable:

``` bash
python -m database.init_db
python -m database.seed_data
```

The initialization command should: 1. Load environment configuration. 2.
Create an engine and session factory. 3. Create tables for a fresh
database. 4. Seed demo records only when requested and only if the seed
has not already been applied. 5. Print a concise summary of inserted or
existing records.

### Fictional organization

Use the fictional company **Northstar Services Group**, a mid-sized
service organization with five departments:

1.  Customer Operations
2.  Finance
3.  People & Culture
4.  Technology
5.  Sales & Partnerships

Create at least 15 initiatives distributed across these departments,
with varied priorities, owners, target dates, progress values, and
statuses. Use synthetic employee names and `example.com` email
addresses.

### Required sample-state coverage

  ---------------------------------------------------------------------
  Scenario                           Seed data requirement
  ---------------------------------- ----------------------------------
  Completed                          At least 2 completed initiatives
                                     with 100% progress

  On track                           At least 3 initiatives with recent
                                     updates and reasonable progress

  Delayed                            At least 2 initiatives with
                                     overdue incomplete milestones

  At risk                            At least 2 initiatives with
                                     negative progress variance

  Blocked                            At least 1 initiative with a
                                     blocked prerequisite/dependency

  Pending decision                   At least 2 pending leadership
                                     decisions

  Overdue action                     At least 2 incomplete actions with
                                     past deadlines

  Upcoming review                    At least 1 scheduled management
                                     meeting
  ---------------------------------------------------------------------

The seed dataset must be internally consistent: - Every initiative
department and owner must exist. - An initiative owner should belong to
the initiative's department. - Every milestone's initiative and owner
must exist. - Completed milestones must have actual completion dates. -
Completed initiatives must have 100% progress. - Every dependency must
reference two different existing initiatives. - All date relationships
must be plausible relative to the demo reporting date. - Seed dates
should be generated relative to a fixed `DEMO_AS_OF_DATE` (configurable)
so the demo does not become stale immediately. For a live demo, allow
the user to select an as-of date.

### Sample CSV templates

Store header-only templates or small clearly labelled sample files in
`sample_data/`. Use stable initiative codes such as `INI-0001`. Keep
CSVs UTF-8 encoded and document date format as ISO `YYYY-MM-DD`.

------------------------------------------------------------------------

## 18. Running the application

``` bash
streamlit run app.py
```

Open the local URL printed by Streamlit (typically
`http://localhost:8501`).

Suggested first-run sequence: 1. Confirm `.env` values. 2. Initialize
the database. 3. Seed synthetic data. 4. Open Executive Command Center.
5. Select the demo reporting date. 6. Open Risk Intelligence and inspect
the reason codes behind flagged initiatives. 7. Update an initiative or
close an action. 8. Confirm that dashboard metrics and exception lists
refresh. 9. Export an Excel view and a PDF executive summary.

------------------------------------------------------------------------

## 19. Testing strategy

Use `pytest`. Business logic should be testable without running the
Streamlit server.

### Test matrix

  -----------------------------------------------------------------------
  Area                    Test                    Expected result
  ----------------------- ----------------------- -----------------------
  KPI                     Completion rate with    Exact expected
                          known records           percentage

  KPI                     Empty denominator       No-data result / safe
                                                  zero internally

  KPI                     Expected progress       0%
                          before start            

  KPI                     Expected progress after 100%
                          target                  

  KPI                     Same-day start and      No division-by-zero
                          target                  

  KPI                     Completed initiative    Expected progress 100%

  Risk                    Each risk trigger       Correct points and
                          independently           reason

  Risk                    Multiple triggers       Correct summed score
                                                  and classification

  Risk                    Score upper bound       Never exceeds 100

  Milestone               Past planned date and   Overdue
                          incomplete              

  Milestone               Past planned date and   Not overdue
                          completed               

  Initiative              Complete with           Transition rejected
                          unfinished milestones   

  Initiative              Complete with all       Transition accepted
                          required milestones     
                          complete                

  Import                  Missing required column Workbook rejected with
                                                  explanation

  Import                  Invalid                 Row-level validation
                          date/status/progress    error

  Import                  Duplicate initiative    Duplicate flagged; no
                          code                    silent overwrite

  Import                  Valid workbook          Preview then successful
                                                  transaction

  AI                      API key absent          Deterministic fallback

  AI                      API timeout/invalid     Deterministic fallback
                          response                

  Database                Empty database          Helpful empty states;
                                                  no crash

  Seed                    Run seed twice          No duplicate records
  -----------------------------------------------------------------------

### Example test command

``` bash
pytest -q
```

### Definition of done for a service

-   Valid input returns the expected result.
-   Invalid input raises a domain-specific exception or returns
    structured validation errors.
-   Database changes are committed or rolled back atomically.
-   At least one happy-path and one edge-case test exist.
-   The UI handles service errors without exposing secrets or stack
    traces.

------------------------------------------------------------------------

## 20. Implementation roadmap

Build a working operational core before adding AI or external
automation. The time estimates below assume focused work with an AI
coding assistant and familiarity with Python; they are targets, not
guarantees.

### Phase 1 --- Project setup and database schema

**Objective:** Establish a runnable Streamlit application and relational
schema.

**Files:** `app.py`, `config.py`, `.env.example`, `requirements.txt`,
`database/connection.py`, `database/models.py`, `database/init_db.py`.

**Tasks** - Create the virtual environment and install dependencies. -
Implement environment configuration and logging. - Define SQLAlchemy
models, enums/check constraints, relationships, and indexes. - Create
engine/session context manager. - Add a database initialization command.

**Dependencies:** None.

**Acceptance criteria** - `streamlit run app.py` starts. - Database
initialization creates all tables in SQLite. - A test can create and
query a department and initiative. - No secrets are hardcoded.

**Tests** - Model constraint tests. - Session creation/closure test. -
Fresh database initialization test.

### Phase 2 --- Sample data and database operations

**Objective:** Create a credible, repeatable fictional dataset.

**Files:** `database/seed_data.py`, `sample_data/*.csv`,
`services/initiative_service.py`, `services/milestone_service.py`,
`services/action_service.py`.

**Tasks** - Seed five departments, employees, at least 15 initiatives,
milestones, updates, dependencies, actions, decisions, KPIs, and a
management meeting. - Ensure seed is idempotent. - Implement
create/read/update service operations. - Add basic form and import
validation utilities.

**Dependencies:** Phase 1.

**Acceptance criteria** - Seed command reports inserted/existing record
counts. - Running seed twice does not duplicate records. - All required
scenario types are present. - Foreign-key and date consistency checks
pass.

**Tests** - Seed idempotency. - Relationship integrity. - Required
scenario coverage.

### Phase 3 --- Executive dashboard and KPI calculations

**Objective:** Deliver a useful leadership overview.

**Files:** `services/kpi_service.py`,
`pages/1_Executive_Command_Center.py`, `utils/formatting.py`.

**Tasks** - Implement all formulas in Section 8 using explicit
`as_of_date`. - Add filters and KPI cards. - Add status, department,
monthly progress, risk, and overdue milestone charts. - Implement empty
states and filter consistency.

**Dependencies:** Phases 1--2.

**Acceptance criteria** - Dashboard values reconcile with database
records. - Changing department/date filters changes relevant cards and
charts. - No-data states are clear. - Each KPI has a documented
definition.

**Tests** - KPI test matrix. - Filter-scope tests. - Empty-dataset
tests.

### Phase 4 --- Initiative and milestone tracking

**Objective:** Let users manage execution records and history.

**Files:** `services/initiative_service.py`,
`services/milestone_service.py`, `pages/2_Initiative_Tracker.py`,
`utils/validators.py`.

**Tasks** - Build initiative list, search, filters, detail view, and
create/edit forms. - Add milestone CRUD and update history. - Enforce
status transitions and completion rules. - Add dependency selection and
display. - Record initiative updates with author and date.

**Dependencies:** Phases 1--3.

**Acceptance criteria** - User can create and update an initiative and
its milestones. - Invalid dates and progress values are rejected. -
Update history is retained. - Completion transition cannot bypass
incomplete milestones.

**Tests** - Status transition tests. - Date/progress validation. -
Milestone completion rules.

### Phase 5 --- Risk and execution intelligence

**Objective:** Surface transparent, actionable delivery exceptions.

**Files:** `services/risk_engine.py`, `pages/3_Risk_Intelligence.py`,
`config.py`.

**Tasks** - Implement configurable risk weights and thresholds. -
Calculate trigger reasons, score, classification, and action
recommendations. - Create exception report with filters. - Add
initiative detail drill-through. - Show as-of date and scoring
explanation.

**Dependencies:** Phases 1--4.

**Acceptance criteria** - Every risk flag has a visible reason. - Score
is reproducible for a fixed dataset and date. - Rules are not described
as predictive AI. - Users can filter and export exceptions.

**Tests** - Each rule independently. - Combined triggers and
classification boundaries. - Missing update and blocked dependency
cases.

### Phase 6 --- Leadership action and decision tracker

**Objective:** Establish follow-through and decision traceability.

**Files:** `services/action_service.py`, `services/decision_service.py`,
`pages/4_Leadership_Actions.py`.

**Tasks** - Build action list and owner-wise views. - Derive overdue
state from deadline and completion status. - Add action creation,
update, completion, and comments. - Record decisions with
pending/approved/rejected status. - Link meeting, initiative, decision,
and action records.

**Dependencies:** Phases 1--4.

**Acceptance criteria** - Pending decisions and overdue actions are
visible. - Completed actions require completion date. - Closure rate
reconciles with stored actions. - Ownership is visible on every open
action.

**Tests** - Overdue derivation. - Completion and closure-rate
calculations. - Decision status transitions.

### Phase 7 --- AI executive reporting and meeting preparation

**Objective:** Generate leadership-ready narratives and agendas from
verified data.

**Files:** `services/reporting_service.py`, `services/ai_service.py`,
`pages/5_Executive_Reports.py`, `pages/6_Management_Reviews.py`.

**Tasks** - Create a typed/validated report payload. - Implement
deterministic weekly summary first. - Add Gemini integration behind an
explicit feature flag and consent action. - Validate AI response and use
fallback on any failure. - Generate meeting agenda from open actions,
risks, decisions, and upcoming milestones.

**Dependencies:** Phases 1--6.

**Acceptance criteria** - Reports show reporting period and data
timestamp. - AI cannot alter verified numeric metrics. - AI-disabled and
API-failure paths work. - Agenda items link back to source records.

**Tests** - Payload calculation. - Missing key, timeout, invalid
response fallback. - AI output validation. - Agenda generation with
empty and populated data.

### Phase 8 --- Import/export, hardening, and deployment

**Objective:** Make the demonstration reproducible and presentable.

**Files:** `utils/exporters.py`, `utils/validators.py`, tests,
`.streamlit/config.toml`, deployment documentation.

**Tasks** - Add Excel templates and import preview/error reporting. -
Add filtered Excel export and PDF report. - Run all tests and resolve
defects. - Add app configuration, secrets, and hosted database setup. -
Deploy to Streamlit Community Cloud with synthetic data. - Capture
screenshots and record a short demo walkthrough.

**Dependencies:** Phases 1--7 for complete scope. Excel/PDF can be
implemented earlier if needed for the MVP.

**Acceptance criteria** - Invalid imports do not partially corrupt the
database. - Export respects filters and includes report metadata. -
Deployment uses secrets, not committed credentials. - Public demo
contains only synthetic data. - README setup instructions work on a
clean machine.

**Tests** - Import schema, duplicates, invalid values, transaction
rollback. - Excel workbook structure. - PDF generation smoke test. -
Full regression: `pytest -q`.

### Recommended rapid-build order

For a 2--3 day prototype, prioritize: 1. Database models + seed data. 2.
KPI functions + executive dashboard. 3. Initiative/milestone tracker. 4.
Risk engine + exception table. 5. Leadership action tracker. 6. Excel
export + PDF summary. 7. Testing, README verification, and deployment.

Implement Gemini and n8n only after the deterministic workflow works end
to end.

------------------------------------------------------------------------

## 21. MVP acceptance checklist

### Functional

-   [ ] Executive dashboard shows accurate initiative, milestone, risk,
    action, and decision metrics.
-   [ ] At least five departments and 15 internally consistent
    initiatives are seeded.
-   [ ] Users can create and update initiatives.
-   [ ] Users can create and update milestones.
-   [ ] Initiative updates are stored as history.
-   [ ] Risk engine detects each documented signal and explains its
    score.
-   [ ] Leadership actions have owners, deadlines, and derived overdue
    state.
-   [ ] Pending decisions are visible.
-   [ ] Management agenda consolidates current exceptions and actions.
-   [ ] CSV/Excel import validates rows before commit.
-   [ ] Excel and PDF exports work.

### Quality

-   [ ] No hardcoded secrets.
-   [ ] Service-layer validation is implemented.
-   [ ] Database writes use transactions.
-   [ ] Empty states and errors are handled.
-   [ ] Automated tests cover KPI and risk logic.
-   [ ] Demo records are clearly synthetic.
-   [ ] A fresh setup can be completed using this README.

------------------------------------------------------------------------

## 22. Fictional demonstration scenario

### Organization

**Northstar Services Group** has five departments: Customer Operations,
Finance, People & Culture, Technology, and Sales & Partnerships. It is
preparing for a weekly operating review.

### Scenario seeded in the database

  -----------------------------------------------------------------------
  Event                   Example seeded          Alignly response
                          condition               
  ----------------------- ----------------------- -----------------------
  High-priority           Customer onboarding     Progress variance is
  initiative delayed      redesign has 48% actual -27 percentage points;
                          progress while          behind-schedule signal
                          time-based expected     adds 25 points
                          progress is 75%         

  Overdue milestone       Process mapping         Overdue milestone
                          milestone planned       signal adds 30 points
                          before the selected     and appears in
                          reporting date and not  exception list
                          completed               

  Blocked dependency      Customer onboarding     Blocked dependency
                          redesign depends on a   signal adds 20 points
                          technology integration  
                          initiative marked       
                          Blocked                 

  Pending leadership      Leadership must approve Decision appears in
  decision                temporary               pending-decision count
                          implementation capacity and management agenda

  Department behind plan  Customer Operations has Department view exposes
                          multiple delayed        lower completion and
                          initiatives and overdue higher overdue count
                          milestones              

  Management review       Weekly operating review Meeting-preparation
  scheduled               has a future meeting    page builds agenda from
                          date                    current exceptions
  -----------------------------------------------------------------------

The scenario should use fixed, documented sample dates and a visible
reporting date so that the expected outputs are reproducible. The
example values above describe the scenario; actual dashboard numbers
must come from the seeded records.

### How the Chief of Staff uses Alignly

1.  Open the Executive Command Center and set the reporting date.
2.  Identify the department with the largest overdue milestone count.
3.  Open Risk Intelligence and inspect the reason codes for the delayed
    onboarding initiative.
4.  Confirm the blocked technology dependency and identify its owner.
5.  Open Leadership Actions and check whether the capacity decision has
    a named decision owner and deadline.
6.  Generate the management review agenda.
7.  Add explicit actions: unblock the integration, agree a recovery
    plan, and resolve the capacity decision.
8.  At the next review, check action closure and whether progress
    variance has improved.

This demonstrates the product's core value: it connects operational
signals to owners, decisions, and follow-through rather than merely
displaying charts.

------------------------------------------------------------------------

## 23. Deployment guide

### Supabase PostgreSQL

1.  Create a Supabase project.
2.  Obtain the PostgreSQL connection string from project database
    settings.
3.  Use the SQLAlchemy psycopg URL form:
    `postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require`
4.  Store it as `DATABASE_URL` in deployment secrets.
5.  Run initialization and seed commands from a trusted local
    environment or a controlled one-off deployment command.
6.  Verify the app can read/write expected demo records.

Never expose the database password in a screenshot, repository, or
client-side code.

### Streamlit Community Cloud

1.  Push the repository to GitHub.
2.  Create a Streamlit Community Cloud app pointing to `app.py`.
3.  Add `DATABASE_URL`, timezone, and optional feature flags through
    Streamlit secrets.
4.  Keep Gemini disabled unless intentionally configured.
5.  Confirm the public deployment uses synthetic data only.
6.  Test database connectivity, imports, exports, and empty/error
    states.

Example `.streamlit/secrets.toml` for local Streamlit use:

``` toml
DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
APP_TIMEZONE = "Asia/Kolkata"
ENABLE_AI_REPORTING = false
```

Do not commit `secrets.toml`.

### Deployment caveats

-   Streamlit Community Cloud is suitable for a portfolio demonstration,
    not a guarantee of production-grade uptime.
-   Confirm Supabase connection limits and pooling guidance for the
    selected plan.
-   Use migrations before evolving a database with retained data.
-   Back up data before schema changes.
-   Avoid publicly exposing write operations without authentication and
    access control.

------------------------------------------------------------------------

## 24. Screenshots

Add real screenshots after implementing the corresponding pages. Do not
include mock screenshots as evidence of implemented functionality.

  -----------------------------------------------------------------------------
  Screenshot                     Suggested file
  ------------------------------ ----------------------------------------------
  Executive Command Center       `assets/screenshots/executive-dashboard.png`

  Initiative Tracker and detail  `assets/screenshots/initiative-tracker.png`
  view                           

  Risk Intelligence exception    `assets/screenshots/risk-intelligence.png`
  report                         

  Leadership Actions             `assets/screenshots/leadership-actions.png`

  Executive PDF report           `assets/screenshots/executive-report.png`

  Management Review agenda       `assets/screenshots/management-review.png`
  -----------------------------------------------------------------------------

Example Markdown once screenshots exist:

``` markdown
![Alignly Executive Dashboard](assets/screenshots/executive-dashboard.png)
```

------------------------------------------------------------------------

## 25. Limitations and assumptions

-   The initial version is a single-organization demonstration using
    synthetic data.
-   Risk scores are heuristic prioritization scores, not failure
    probabilities.
-   Expected progress assumes a linear time-based delivery plan; real
    initiatives may not progress linearly.
-   Initiative progress is manually maintained and is not automatically
    inferred from milestone counts.
-   The application depends on data quality and timely owner updates.
-   No live integrations with email, calendar, ERP, HRIS, CRM, or
    project-management systems are included in the MVP.
-   Gemini output can be incomplete or incorrect; it must be reviewed
    and must never be treated as the source of truth.
-   n8n reminders are optional and require separate deployment and
    credential management.
-   Authentication, fine-grained authorization, multi-tenancy, and
    enterprise audit controls are outside the initial scope.

------------------------------------------------------------------------

## 26. Future enhancements

Prioritize enhancements based on user feedback rather than adding
technology for its own sake.

1.  **Role-based access control:** Executive, department head,
    initiative owner, and read-only roles.
2.  **Audit trail:** Immutable history for status, owner, target-date,
    and decision changes.
3.  **Weighted milestone progress:** Optional weights with validation
    and transparent roll-up.
4.  **Portfolio dependency graph:** Visualize cross-department
    dependencies and critical paths.
5.  **Historical trend analysis:** Compare risk, delivery variance, and
    closure rates over time.
6.  **Calendar integration:** Sync management reviews and key deadlines.
7.  **Email/Slack/Teams notifications:** Notify owners through approved
    channels.
8.  **External data ingestion:** Controlled imports from
    project-management or CRM systems.
9.  **Configurable risk policies:** Admin-managed thresholds with
    versioned scoring policies.
10. **PowerPoint management pack:** Generate a slide deck from verified
    report data.
11. **Multi-workspace support:** Separate organizations with tenant
    isolation and authorization.
12. **Forecasting:** Only after sufficient historical data exists;
    validate models and communicate uncertainty.

------------------------------------------------------------------------

## 27. Learning outcomes

Building Alignly demonstrates practical ability to:

-   Translate an ambiguous organizational problem into product
    requirements.
-   Design relational data models and enforce referential integrity.
-   Implement KPI definitions and reproducible business calculations.
-   Build an operational dashboard with meaningful filters and
    visualizations.
-   Design a transparent exception and risk-scoring framework.
-   Connect delivery risks to accountable owners, decisions, and
    actions.
-   Validate spreadsheet data and create reliable reporting exports.
-   Integrate an LLM with grounding, privacy controls, validation, and
    deterministic fallback.
-   Structure a Python application into UI, service, data, and utility
    layers.
-   Test business logic and edge cases with pytest.
-   Deploy a data-backed application using managed PostgreSQL and
    environment-based secrets.
-   Communicate operational findings in a concise, executive-friendly
    format.

------------------------------------------------------------------------

## Product definition of done

Alignly is ready for a portfolio demonstration when a reviewer can load
the synthetic organization, identify a delayed strategic initiative,
inspect the underlying risk reasons, trace a blocked dependency, find
the pending leadership decision, assign or review an accountable action,
and export a management-ready summary --- with all displayed metrics
traceable to the underlying records.

**The standard is not the number of charts or AI features. The standard
is whether the application helps a leadership team see what is off
track, understand why, and decide what happens next.**
