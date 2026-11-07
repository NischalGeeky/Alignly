# services/risk_import_service.py
"""Service for importing Risks from CSV/Excel files.

Mirrors the pattern used for Initiative and Milestone imports, handling:
- CSV and Excel file parsing.
- Column name normalisation.
- Validation of required fields, severity, status, dates, and foreign‑key references.
- Duplicate detection within the uploaded file and against the database.
- Returning a summary dictionary compatible with the import endpoint.
"""

import io
import uuid
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy.orm import Session

from database import models
from api.schemas.risk import RiskCreate

# Accepted column names (case‑insensitive) mapped to the fields of RiskCreate.
COLUMN_MAP = {
    "initiative_id": "initiative_id",
    "title": "title",
    "description": "description",
    "severity": "severity",
    "status": "status",
    "identified_date": "identified_date",
}

REQUIRED_COLUMNS = {"initiative_id", "title", "severity", "status", "identified_date"}

ALLOWED_SEVERITY = {"Low", "Medium", "High", "Critical"}
ALLOWED_STATUS = {"Open", "Mitigated", "Closed"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower‑case column names, replace spaces with underscores and map to model fields."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    mapped = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[col]
        else:
            mapped[col] = col
    df = df.rename(columns=mapped)
    return df


def _validate_row(row: pd.Series, db: Session) -> List[str]:
    """Validate a single row according to the Risk model requirements.

    Returns a list of error messages – empty if the row passes validation.
    """
    errors: List[str] = []
    # Required fields present
    for field in REQUIRED_COLUMNS:
        if pd.isna(row.get(field)):
            errors.append(f"Missing required field '{field}'")
    # Validate initiative_id UUID and existence
    val = row.get("initiative_id")
    if not pd.isna(val):
        try:
            uid = uuid.UUID(str(val))
            exists = db.query(models.Initiative).filter(models.Initiative.id == uid).first()
            if not exists:
                errors.append("initiative_id does not reference an existing Initiative")
        except Exception:
            errors.append("Invalid UUID format for 'initiative_id'")
    # Severity validation
    sev = row.get("severity")
    if not pd.isna(sev) and str(sev) not in ALLOWED_SEVERITY:
        errors.append(f"severity must be one of {', '.join(sorted(ALLOWED_SEVERITY))}")
    # Status validation
    st = row.get("status")
    if not pd.isna(st) and str(st) not in ALLOWED_STATUS:
        errors.append(f"status must be one of {', '.join(sorted(ALLOWED_STATUS))}")
    # identified_date validation
    date_val = row.get("identified_date")
    if not pd.isna(date_val):
        if isinstance(date_val, (datetime, pd.Timestamp)):
            pass
        else:
            try:
                datetime.strptime(str(date_val), "%Y-%m-%d")
            except Exception:
                errors.append("Invalid date format for 'identified_date' (expected YYYY-MM-DD)")
    return errors


def import_risks(file_bytes: bytes, filename: str, db: Session) -> Dict[str, Any]:
    """Import risks from a CSV or Excel file.

    Returns a summary dict with keys: total, imported, duplicates, rejected, errors.
    """
    ext = filename.split('.')[-1].lower()
    if ext not in {"csv", "xlsx", "xls"}:
        raise ValueError("Unsupported file extension. Use CSV or Excel.")

    stream = io.BytesIO(file_bytes)
    if ext == "csv":
        df = pd.read_csv(stream)
    else:
        df = pd.read_excel(stream)

    if df.empty:
        return {"total": 0, "imported": 0, "duplicates": 0, "rejected": 0, "errors": []}

    df = _normalize_columns(df)
    total_rows = len(df)
    imported = 0
    duplicates = 0
    rejected = 0
    error_details: List[Dict[str, Any]] = []

    # Track duplicates within file by (initiative_id, title)
    seen_keys = set()
    for idx, row in df.iterrows():
        row_number = idx + 2  # header is row 1
        # Missing columns early detection
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            error_details.append({"row": row_number, "messages": [f"Missing columns: {', '.join(sorted(missing_cols))}"]})
            rejected = total_rows
            break
        # Duplicate detection within file
        key = (str(row.get("initiative_id")).strip(), str(row.get("title")).strip())
        if not pd.isna(row.get("initiative_id")) and not pd.isna(row.get("title")):
            if key in seen_keys:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate risk (initiative_id + title) within import file"]})
                continue
            seen_keys.add(key)
        # Duplicate detection against DB
        if not pd.isna(row.get("initiative_id")) and not pd.isna(row.get("title")):
            existing = (
                db.query(models.Risk)
                .filter(models.Risk.initiative_id == uuid.UUID(str(row["initiative_id"])) )
                .filter(models.Risk.title == str(row["title"]).strip())
                .first()
            )
            if existing:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate risk already exists in database"]})
                continue
        # Validate other fields
        row_errors = _validate_row(row, db)
        if row_errors:
            rejected += 1
            error_details.append({"row": row_number, "messages": row_errors})
            continue
        # Build payload for Pydantic validation
        try:
            payload = {
                "initiative_id": uuid.UUID(str(row["initiative_id"])),
                "title": str(row["title"]).strip(),
                "description": row.get("description"),
                "severity": str(row["severity"]).strip(),
                "status": str(row["status"]).strip(),
                "identified_date": pd.to_datetime(row["identified_date"]).date(),
            }
            RiskCreate(**payload)
        except Exception as exc:
            rejected += 1
            error_details.append({"row": row_number, "messages": [f"Pydantic validation error: {exc}"]})
            continue
        # Persist
        risk = models.Risk(**payload)
        db.add(risk)
        imported += 1
    if imported:
        db.commit()
    return {
        "total": total_rows,
        "imported": imported,
        "duplicates": duplicates,
        "rejected": rejected,
        "errors": error_details,
    }
