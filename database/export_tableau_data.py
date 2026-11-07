# database/export_tableau_data.py
"""Entry‑point to (re)create analytical SQLite views and export them for Tableau.

Usage:
    python -m database.export_tableau_data
"""
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.connection import engine
from services.tableau_export_service import export_views, VIEW_NAMES

SQL_VIEWS_PATH = Path(__file__).resolve().parent / "analytics_views.sql"


def _run_sql_script() -> None:
    """Execute the SQL file that defines the analytical views.

    The file contains a series of ``CREATE VIEW IF NOT EXISTS`` statements.
    SQLite allows executing the whole script in a single ``executescript``
    call, but SQLAlchemy's ``execute`` only accepts a single statement.
    Therefore we read the file and execute each statement individually.
    """
    if not SQL_VIEWS_PATH.is_file():
        raise FileNotFoundError(f"Analytics SQL file not found: {SQL_VIEWS_PATH}")

    script = SQL_VIEWS_PATH.read_text(encoding="utf-8")
    # Split on semicolon that terminates a statement – keep any trailing whitespace.
    statements = [s.strip() for s in script.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Failed to execute statement: {stmt[:60]}...\n{exc}")


def main() -> None:
    try:
        _run_sql_script()
        counts = export_views()
        for view in VIEW_NAMES:
            csv_path = Path(__file__).resolve().parents[1] / "exports" / "tableau" / f"{view}.csv"
            row_cnt = counts.get(view, 0)
            print(f"{view}.csv -> {row_cnt} rows written to {csv_path}")
    except Exception as exc:
        print(f"Error during Tableau export: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
