# services/initiative_import_service.py
"""Service for importing Initiatives from CSV/Excel files.

The service reads a file using pandas, normalises column names, validates each row
against the Initiative model constraints and foreign‑key references, detects
duplicates (both within the file and against existing records) and returns a
summary dictionary.
"""

import io
import uuid
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
from sqlalchemy.orm import Session

from database import models
from api.schemas.initiative import InitiativeCreate

# Mapping of accepted column names (case‑insensitive) to the field names expected by
# InitiativeCreate.  The import can contain either the exact field name or a
# human‑readable variant (e.g. "dept_id" -> "department_id").
COLUMN_MAP = {
    "code": "code",
    "department_id": "department_id",
    "owner_id": "owner_id",
    "name": "name",
    "description": "description",
    "strategic_objective": "strategic_objective",
    "expected_outcome": "expected_outcome",
    "priority": "priority",
    "start_date": "start_date",
    "target_date": "target_date",
    "status": "status",
    "progress_pct": "progress_pct",
}

REQUIRED_COLUMNS = {"code", "department_id", "owner_id", "name", "start_date", "target_date", "progress_pct"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower‑case column names, replace spaces with underscores and map to model fields."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Apply the mapping for any alternative names
    mapped = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[col]
        else:
            # keep as‑is; validation will later reject unknown columns
            mapped[col] = col
    df = df.rename(columns=mapped)
    return df


def _validate_row(row: pd.Series, db: Session) -> List[str]:
    """Validate a single row.

    Returns a list of error messages – empty if the row is valid.
    """
    errors: List[str] = []
    # Check required fields
    for field in REQUIRED_COLUMNS:
        if pd.isna(row.get(field)):
            errors.append(f"Missing required field '{field}'")
    # Validate UUID fields
    for uuid_field in ("department_id", "owner_id"):
        val = row.get(uuid_field)
        if not pd.isna(val):
            try:
                uid = uuid.UUID(str(val))
                # Verify existence in DB
                if uuid_field == "department_id":
                    exists = db.query(models.Department).filter(models.Department.id == uid).first()
                else:
                    exists = db.query(models.Employee).filter(models.Employee.id == uid).first()
                if not exists:
                    errors.append(f"{uuid_field} does not reference an existing record")
            except Exception:
                errors.append(f"Invalid UUID format for '{uuid_field}'")
    # Validate dates
    for date_field in ("start_date", "target_date"):
        val = row.get(date_field)
        if not pd.isna(val):
            if isinstance(val, (datetime, pd.Timestamp)):
                # ok, pandas will give Timestamp
                continue
            try:
                datetime.strptime(str(val), "%Y-%m-%d")
            except Exception:
                errors.append(f"Invalid date format for '{date_field}' (expected YYYY-MM-DD)")
    # progress_pct range
    prog = row.get("progress_pct")
    if not pd.isna(prog):
        try:
            prog_int = int(prog)
            if not (0 <= prog_int <= 100):
                errors.append("progress_pct must be between 0 and 100")
        except Exception:
            errors.append("progress_pct must be an integer")
    # target_date after start_date
    if not pd.isna(row.get("start_date")) and not pd.isna(row.get("target_date")):
        try:
            start = pd.to_datetime(row["start_date"]).date()
            target = pd.to_datetime(row["target_date"]).date()
            if target < start:
                errors.append("target_date must be on or after start_date")
        except Exception:
            pass
    return errors


def import_initiatives(file_bytes: bytes, filename: str, db: Session) -> Dict[str, Any]:
    """Import initiatives from a CSV or Excel file.

    Parameters
    ----------
    file_bytes: Raw bytes of the uploaded file.
    filename: Original filename (used to decide file type).
    db: SQLAlchemy session.

    Returns
    -------
    dict with keys: total, imported, duplicates, rejected, errors (list of
    {row: int, messages: List[str]}).
    """
    # Determine file type
    ext = filename.split('.')[-1].lower()
    if ext not in {"csv", "xlsx", "xls"}:
        raise ValueError("Unsupported file extension. Use CSV or Excel.")

    # Load into pandas DataFrame
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

    # Track codes seen in this file to catch intra‑file duplicates
    seen_codes = set()
    for idx, row in df.iterrows():
        row_number = idx + 2  # +2 to account for header row (1‑based indexing)
        # Detect missing required columns early
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            # All rows share this error – break early
            error_details.append({"row": row_number, "messages": [f"Missing columns: {', '.join(sorted(missing_cols))}"]})
            rejected = total_rows
            break
        # Duplicate code within file
        code = row.get("code")
        if pd.isna(code):
            # code is required – will be caught by validation below
            pass
        else:
            code_str = str(code).strip()
            if code_str in seen_codes:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate code within import file"]})
                continue
            seen_codes.add(code_str)
        # Duplicate against DB
        if not pd.isna(code):
            existing = db.query(models.Initiative).filter(models.Initiative.code == str(code)).first()
            if existing:
                duplicates += 1
                error_details.append({"row": row_number, "messages": ["Duplicate code already exists in database"]})
                continue
        # Validate remaining fields
        row_errors = _validate_row(row, db)
        if row_errors:
            rejected += 1
            error_details.append({"row": row_number, "messages": row_errors})
            continue
        # Build InitiativeCreate model – let Pydantic handle type coercion
        try:
            payload = {
                "code": str(row["code"]).strip(),
                "department_id": uuid.UUID(str(row["department_id"])),
                "owner_id": uuid.UUID(str(row["owner_id"])),
                "name": str(row["name"]).strip(),
                "description": row.get("description"),
                "strategic_objective": row.get("strategic_objective"),
                "expected_outcome": row.get("expected_outcome"),
                "priority": row.get("priority", "Medium"),
                "start_date": pd.to_datetime(row["start_date"]).date(),
                "target_date": pd.to_datetime(row["target_date"]).date(),
                "status": row.get("status", "Not Started"),
                "progress_pct": int(row["progress_pct"]),
            }
            legit = InitiativeCreate(**payload)
        except Exception as exc:
            rejected += 1
            error_details.append({"row": row_number, "messages": [f"Pydantic validation error: {exc}"]})
            continue
        # Persist
        initiative = models.Initiative(**legit.model_dump())
        db.add(initiative)
        imported += 1
    # Commit once at the end (if any were added)
    if imported:
        db.commit()
    return {
        "total": total_rows,
        "imported": imported,
        "duplicates": duplicates,
        "rejected": rejected,
        "errors": error_details,
    }
