# Alignly — Business Operations & Executive Intelligence Platform

> **A practical operations command center for tracking strategic execution, surfacing delivery risks, maintaining leadership accountability, and preparing management reviews.**

---

## Architecture & Implementation Overview

Alignly establishes a modular Python application with SQLAlchemy 2.x declarative models, SQLite local development, PostgreSQL compatibility, idempotent synthetic dataset seeding, and a polished corporate Streamlit interface.

### Project Structure

```text
Alignly/
├── app.py                      # Streamlit application entry point
├── config.py                   # Environment configuration & reference date management
├── requirements.txt            # Project dependencies
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules (secrets, DBs, cache)
├── README.md                   # Project documentation & execution guide
├── Alignly_README.md           # Master technical specification
│
├── database/
│   ├── __init__.py
│   ├── connection.py           # SQLAlchemy 2.x engine, SessionLocal & context manager
│   ├── models.py               # Complete relational models & database constraints
│   ├── init_db.py              # CLI database schema creation utility
│   └── seed_data.py            # Idempotent synthetic dataset seeder for Northstar Services Group
│
├── sample_data/                # Synthetic business operational datasets (ISO/relative offsets)
│   ├── departments.csv
│   ├── employees.csv
│   ├── initiatives.csv
│   ├── milestones.csv
│   ├── initiative_updates.csv
│   ├── initiative_dependencies.csv
│   ├── leadership_actions.csv
│   ├── leadership_decisions.csv
│   ├── management_meetings.csv
│   ├── kpi_definitions.csv
│   ├── kpi_measurements.csv
│   └── risks.csv
│
├── services/
│   └── __init__.py             # Service layer placeholder for future business logic
│
├── pages/
│   └── README.md               # Streamlit multi-page module placeholder
│
├── utils/
│   ├── __init__.py
│   └── logging_config.py       # Centralized application logging
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # Isolated SQLite in-memory fixture with PRAGMA foreign keys
    ├── test_database.py        # Database schema, model & constraint tests (Task 1)
    └── test_seed_data.py       # Synthetic data integrity, scenario & idempotency tests (Task 2)
```

---

## Quickstart & Execution Instructions

### 1. Prerequisites & Environment Setup

Ensure Python 3.10+ (or 3.11+) is installed. Install the dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` if custom parameters are required:

```bash
cp .env.example .env
```

Environment variables:
- `DATABASE_URL`: Defaults to SQLite at `alignly.db` in repository root. For PostgreSQL: `postgresql+psycopg2://<user>:<password>@<host>:<port>/<dbname>`.
- `DEMO_AS_OF_DATE`: Defaults to `2026-11-01`. All seed dates and status horizons are computed relative to this reference date so the dataset never becomes obsolete.

### 3. Initialize the Database Schema

Run the standalone initialization utility to create all relational tables:

```bash
python -m database.init_db
```

Output:
```text
[YYYY-MM-DD HH:MM:SS] INFO utils.logging_config: Initializing database tables...
[YYYY-MM-DD HH:MM:SS] INFO utils.logging_config: Database tables created successfully.
Success: All database tables created successfully.
```

### 4. Seed Synthetic Business Operational Data (Task 2)

Populate the database with the **Northstar Services Group** synthetic operational dataset:

```bash
python -m database.seed_data
```

Output:
```text
Alignly Seeding — As-Of Date: 2026-11-01

=======================================================
Table                        | Inserted   | Existing  
-------------------------------------------------------
departments                  | 5          | 0         
employees                    | 15         | 0         
management_meetings          | 3          | 0         
kpi_definitions              | 6          | 0         
initiatives                  | 16         | 0         
milestones                   | 48         | 0         
initiative_updates           | 16         | 0         
initiative_dependencies      | 4          | 0         
risks                        | 5          | 0         
leadership_decisions         | 4          | 0         
leadership_actions           | 5          | 0         
kpi_measurements             | 18         | 0         
=======================================================
Total                        | 145        | 0         

Success: Database seeding completed successfully.
```

**Idempotency:** Executing `python -m database.seed_data` a second time inserts 0 duplicates and reports 145 existing records.

### 5. Run the Streamlit Application

Launch the Streamlit web interface:

```bash
streamlit run app.py
```
Or via Python module:
```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` to view the corporate operations command center landing page, active database connectivity status, and configuration details.

### 6. Run Automated Tests

Execute the automated test suite across all implemented modules:

```bash
pytest -q
# or
python -m pytest -q
```

All tests execute in an isolated in-memory SQLite database with foreign-key constraint enforcement (`PRAGMA foreign_keys=ON`).

---

## Synthetic Organization: Northstar Services Group

The dataset models **Northstar Services Group**, a mid-sized services enterprise with five operational departments:

1. **Customer Operations** (3 initiatives, 3 employees, customer SLA & response time metrics)
2. **Finance** (3 initiatives, 3 employees, cashflow dashboard & automated AP invoicing)
3. **People & Culture** (3 initiatives, 3 employees, leadership development & benefits portal)
4. **Technology** (4 initiatives, 3 employees, cloud migration, zero-trust security & API gateway)
5. **Sales & Partnerships** (3 initiatives, 3 employees, partner programs & CRM automation)

### Mandatory Scenario Coverage

The seeded dataset satisfies all mandatory execution scenarios:

| Scenario | Seeded Condition | Verification |
|---|---|---|
| **Completed** | `INI-0001` (ERP Fiscal Close) & `INI-0002` (Benefits Portal) | 100% progress, all milestones completed with actual completion dates |
| **On Track** | `INI-0003`, `INI-0004`, `INI-0005`, etc. | Updated within 2–4 days of `DEMO_AS_OF_DATE`, progress exceeding expected time-based curve |
| **Delayed** | `INI-0006` (Customer Process Mapping) & `INI-0007` (Manager Training) | Incomplete milestones with `planned_date < DEMO_AS_OF_DATE` |
| **At Risk** | `INI-0008` (Customer Onboarding) & `INI-0009` (CDP Integration) | Progress variances of -27% and -35% (actual vs. expected progress) |
| **Blocked Dependency** | `INI-0008` depends on `INI-0010` (Legacy Billing Gateway) | `INI-0010` is `Blocked`, establishing an upstream dependency blocker |
| **Pending Decisions** | Decisions on onboarding contractor surge capacity & cloud migration budget | 2 records with `status = 'Pending'` |
| **Overdue Actions** | Billing vendor API renegotiation (-10d) & process mapping revised schedule (-4d) | 2 incomplete actions with past deadlines |
| **Upcoming Review** | Q4 Executive Review & Strategy Alignment (+7d) | 1 scheduled management meeting |

---

## Database Schema Specification

The 12 relational tables defined in [`database/models.py`](file:///C:/Users/nispa/Desktop/NewProjectIdeas/Alignly/database/models.py):

1. **`departments`**: Organizational units. Unique non-empty `name`.
2. **`employees`**: Team members and accountable owners. Unique `email`, foreign key to `departments`.
3. **`initiatives`**: Strategic work portfolio. Unique `code`, foreign keys to `departments` and `employees`. Check constraints on progress percentage (`0 <= progress_pct <= 100`) and dates (`target_date >= start_date`). Indexed on `(department_id, status)`, `owner_id`, and `target_date`.
4. **`milestones`**: Key deliverables. Foreign keys to `initiatives` and `employees`. Check constraint enforcing `actual_date IS NOT NULL` if `status == 'Completed'`. Indexed on `(initiative_id, planned_date, status)`.
5. **`initiative_updates`**: Dated progress history and logs. Foreign keys to `initiatives` and `employees`. Check constraint for progress (`0 <= progress_pct <= 100`). Indexed on `(initiative_id, update_date)`.
6. **`risks`**: Identified risks and severity. Foreign key to `initiatives`.
7. **`management_meetings`**: Executive review schedules and meeting logs.
8. **`leadership_actions`**: Accountable actions resulting from meetings or initiatives. Foreign keys to `initiatives`, `employees`, and `management_meetings`. Indexed on `(owner_id, deadline, status)`.
9. **`leadership_decisions`**: Recorded decisions. Foreign keys to `initiatives` and `management_meetings`. Indexed on `(status, decision_date)`.
10. **`kpi_definitions`**: KPI metadata, metric units, target direction, and department scoping.
11. **`kpi_measurements`**: Time-series actual and target measurements. Foreign keys to `kpi_definitions` and `departments`. Indexed on `(definition_id, measurement_date, department_id)`.
12. **`initiative_dependencies`**: Association table mapping prerequisites between initiatives. Disallows self-dependency via check constraint.
