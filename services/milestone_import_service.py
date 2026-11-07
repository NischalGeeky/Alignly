# services/milestone_import_service.py
"""Service for importing Milestones from CSV/Excel files.

The implementation mirrors the initiative import service, handling:
- CSV and Excel files (xlsx, xls).
- Normalising column names.
- Validation of required fields, dates, status, and foreign‑key references.
- Duplicate detection within the uploaded file and against existing DB rows.
- Returning a summary dictionary compatible with the existing import endpoint.
"""

import io
import uuid
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy.orm import Session

from database import models
from api.schemas.milestone import MilestoneCreate

# Mapping of accepted column names (case‑insensitive) to the field names expected by MilestoneCreate.
COLUMN_MAP = {
    "initiative_id": "initiative_id",
    "owner_id": "owner_id",
    "name": "name",
    "planned_date": "planned_date",
    "actual_date": "actual_date",
    "status": "status",
    "notes": "notes",
}

REQUIRED_COLUMNS = {"initiative_id", "owner_id", "name", "planned_date", "status"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower‑case column names, replace spaces with underscores and map to model fields."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    mapped = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[col]
        else:
            # Keep as‑is – validation will later reject unknown columns.
            mapped[col] = col
    df = df.rename(columns=mapped)
    return df


def _validate_row(row: pd.Series, db: Session) -> List[str]:
    """Validate a single row using the Pydantic MilestoneCreate schema.

    Returns a list of error messages – empty if the row is valid.
    """
    errors: List[str] = []
    # Check required fields presence
    for field in REQUIRED_COLUMNS:
        if pd.isna(row.get(field)):
            errors.append(f"Missing required field '{field}'")
    # Validate UUID fields (initiative_id, owner_id)
    for uuid_field in ("initiative_id", "owner_id"):
        val = row.get(uuid_field)
        if not pd.isna(val):
            try:
                uid = uuid.UUID(str(val))
                # Verify existence in DB
                if uuid_field == "initiative_id":
                    exists = db.query(models.Initiative).filter(models.Initiative.id == uid).first()
                else:
                    exists = db.query(models.Employee).filter(models.Employee.id == uid).first()
                if not exists:
                    errors.append(f"{uuid_field} does not reference an existing record")
            except Exception:
                errors.append(f"Invalid UUID format for '{uuid_field}'")
    # Validate dates (planned_date, actual_date)
    for date_field in ("planned_date", "actual_date"):
        val = row.get(date_field)
        if not pd.isna(val):
            if isinstance(val, (datetime, pd.Timestamp)):
                continue
            try:
                datetime.strptime(str(val), "%Y-%m-%d")
            except Exception:
                errors.append(f"Invalid date format for '{date_field}' (expected YYYY-MM-DD)")
    # Status validation – rely on Pydantic, but ensure non‑empty string
    status_val = row.get("status")
    if not pd.isna(status_val) and not str(status_val).strip():
        errors.append("status must be a non‑empty string")
    return errors


def import_milestones(file_bytes: bytes, filename: str, db: Session) -> Dict[str, Any]:
    """Import milestones from a CSV or Excel file.

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

    # Track duplicates within file by (initiative_id, name)
    seen_keys = set()
    for idx, row in df.iterrows():
        row_number = idx + 2  # header row is 1
        # Detect missing required columns early
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            error_details.append({"row": row_number, "messages": [f"Missing columns: {', '.join(sorted(missing_cols))}"]})
            rejected = total_rows
            break
        # Duplicate detection within file
        key = (str(row.get("initiative_id")).strip(), str(row.get("name")).strip())
        if pd.isna(row.get("initiative_id")) or pd.isna(row.get("name")):
            # Will be caught by validation later
            pass
        else:
            if key in seen_keys:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate milestone (initiative_id + name) within import file"]})
                continue
            seen_keys.add(key)
        # Duplicate detection against DB
        if not pd.isna(row.get("initiative_id")) and not pd.isna(row.get("name")):
            existing = (
                db.query(models.Milestone)
                .filter(models.Milestone.initiative_id == uuid.UUID(str(row["initiative_id"])) )
                .filter(models.Milestone.name == str(row["name"]).strip())
                .first()
            )
            if existing:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate milestone already exists in database"]})
                continue
        # Validate remaining fields
        row_errors = _validate_row(row, db)
        if row_errors:
            rejected += 1
            error_details.append({"row": row_number, "messages": row_errors})
            continue
        # Build payload for Pydantic validation
        try:
            payload = {
                "initiative_id": uuid.UUID(str(row["initiative_id"])),
                "owner_id": uuid.UUID(str(row["owner_id"])),
                "name": str(row["name"]).strip(),
                "planned_date": pd.to_datetime(row["planned_date"]).date(),
                "actual_date": pd.to_datetime(row["actual_date"]).date() if not pd.isna(row.get("actual_date")) else None,
                "status": str(row["status"]).strip(),
                "notes": row.get("notes"),
            }
            MilestoneCreate(**payload)
        except Exception as exc:
            rejected += 1
            error_details.append({"row": row_number, "messages": [f"Pydantic validation error: {exc}"]})
            continue
        # Persist
        milestone = models.Milestone(**payload)
        db.add(milestone)
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
