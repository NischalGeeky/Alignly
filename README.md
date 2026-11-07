# Alignly — Business Operations & Executive Intelligence Platform

> **A practical operations command center for tracking strategic execution, surfacing delivery risks, maintaining leadership accountability, and preparing management reviews.**

---

## Architecture & Implementation Overview

Alignly is a modular Python application built around:

- **FastAPI** – primary REST API backend.
- **SQLAlchemy 2.x** – declarative ORM with a local SQLite database (default) and optional PostgreSQL compatibility via `DATABASE_URL`.
- **Pandas** – data‑frame processing for import pipelines and Tableau CSV generation.
- **Tableau** – analytical views are exported as CSV files for consumption in Tableau dashboards.

The original Streamlit UI has been removed; all visualisation now lives in Tableau using the exported CSVs.

### Project Structure

```text
Alignly/
├── alignly.db                     # SQLite DB used by the API and export scripts
├── config.py                      # Environment/config handling (DATABASE_URL, demo date)
├── requirements.txt               # Python dependencies
├── .env.example                   # Example env file
├── .gitignore                     # Ignored files (secrets, DB, caches, exports)
├── README.md                      # This documentation file
│
├── api/
│   ├── main.py                    # FastAPI application entry point
│   └── routers/…                  # CRUD routers (initiatives, milestones, risks, …)
│
├── database/
│   ├── connection.py              # SQLAlchemy engine & session helper
│   ├── models.py                  # ORM model definitions
│   ├── init_db.py                 # CLI to create tables
│   ├── seed_data.py               # Idempotent synthetic demo data loader
│   └── analytics_views.sql        # SQLite view definitions for Tableau exports
│
├── services/
│   ├── tableau_export_service.py # Export analytical views to CSV
│   └── …                          # Import services (initiatives, milestones, risks)
│
├── sample_data/                  # Original synthetic CSV assets
│   ├── departments.csv
│   ├── employees.csv
│   ├── initiatives.csv
│   └── …
│
├── exports/tableau/               # Generated Tableau CSVs (auto‑created)
│   ├── vw_initiative_overview.csv
│   ├── vw_milestone_health.csv
│   └── …
│
└── tests/                         # Pytest suite – uses an isolated in‑memory DB
    ├── conftest.py                # Test fixtures (in‑memory SQLite)
    └── …
```

---

## Quickstart & Execution Instructions

### 1. Prerequisites & Environment Setup

```bash
# Python 3.10+ (or 3.11+)
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example env file and adjust if needed:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL` – defaults to `sqlite+pysqlite:///alignly.db`. Set a PostgreSQL DSN for production.
- `DEMO_AS_OF_DATE` – reference date for seeding synthetic data (default `2026-11-01`).

### 3. Initialise the Database Schema

```bash
python -m database.init_db
```

### 4. Seed Synthetic Demo Data

```bash
python -m database.seed_data
```

The seed script is idempotent – re‑running will insert no duplicates.

### 5. Run the FastAPI Service

```bash
uvicorn api.main:app --reload
```

The API will be reachable at `http://127.0.0.1:8000`.

### 6. Generate Tableau Export CSVs

```bash
python -m database.export_tableau_data
```

This command:
1. Executes the analytical view definitions in `database/analytics_views.sql`.
2. Writes each view to `exports/tableau/<view_name>.csv`.
3. Prints row counts per view.

The generated CSVs are ready to be imported into Tableau for dashboard creation.

---

## Tableau Data Dictionary

A detailed description of the exported tables, column semantics, primary‑key candidates, and suggested dimensions/measures lives in:

`docs/tableau_data_dictionary.md`

---

## Testing

All tests run against a **temporary in‑memory SQLite database**; they never touch the on‑disk `alignly.db`.

```bash
pytest -q                # Run full test suite
python -m pytest --collect-only -q   # Verify test collection
```

---

## Project Roadmap

- **Replace Streamlit UI** with Tableau‑based visualisations (completed).
- Add role‑based authentication (future).
- CI/CD pipeline for automated DB migrations and Tableau export verification.

---

## License

[MIT License](LICENSE)
