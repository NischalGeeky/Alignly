# services/tableau_export_service.py
"""Utility to export analytical SQLite views for Tableau.

The module reads the six analytical views defined in
`database/analytics_views.sql`, loads each into a pandas ``DataFrame``,
normalises date columns to ISO‑8601 strings and writes the result to a
CSV file under ``exports/tableau/``.

All CSV files are overwritten on each call – the function returns a
mapping of view name to the number of exported rows.
"""

import os
import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from database.connection import engine

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXPORT_DIR = Path(__file__).resolve().parents[1] / "exports" / "tableau"
VIEW_NAMES: List[str] = [
    "vw_initiative_overview",
    "vw_milestone_health",
    "vw_department_performance",
    "vw_leadership_actions",
    "vw_kpi_measurements",
    "vw_initiative_updates",
]


def _ensure_output_dir() -> None:
    """Create the export directory if it does not exist."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _iso_format_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert any ``date`` or ``datetime`` columns to ISO‑8601 strings.

    ``pandas`` may keep date objects as ``datetime.date``/``datetime.datetime``
    or as ``numpy`` ``datetime64`` objects – both are handled.
    ``None``/``NaN`` values are left untouched.
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Already a datetime64 – format to string preserving NaT as empty
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        else:
            # Fallback: inspect first non‑null value
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            if isinstance(sample, (datetime.date, datetime.datetime)):
                df[col] = df[col].apply(
                    lambda v: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v
                )
    return df


def export_views() -> Dict[str, int]:
    """Export each analytical view to a CSV file.

    Returns
    -------
    dict
        Mapping of view name to the number of rows written.
    """
    _ensure_output_dir()
    exported_counts: Dict[str, int] = {}

    with engine.connect() as conn:
        for view in VIEW_NAMES:
            # Load the view into a DataFrame
            sql = text(f"SELECT * FROM {view}")
            df = pd.read_sql(sql, conn)

            # Normalise dates
            df = _iso_format_dates(df)

            # Write CSV – overwrite any existing file
            out_path = EXPORT_DIR / f"{view}.csv"
            df.to_csv(out_path, index=False)
            exported_counts[view] = len(df)

    return exported_counts


if __name__ == "__main__":
    # Simple manual run for debugging
    counts = export_views()
    for v, c in counts.items():
        print(f"Exported {c} rows to {EXPORT_DIR / f'{v}.csv'}")
