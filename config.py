import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    # Also load from .env.example to aid developers
    env_example = BASE_DIR / ".env.example"
    if env_example.exists():
        load_dotenv(env_example)

# Retrieve the DATABASE_URL; fall back to SQLite in the project root
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # SQLite URL format for Windows/POSIX: normalize slashes
    db_path = (BASE_DIR / "alignly.db").as_posix()
    DATABASE_URL = f"sqlite+pysqlite:///{db_path}"

# Configurable reporting reference date for demonstration and seeding
DEMO_AS_OF_DATE_STR = os.getenv("DEMO_AS_OF_DATE", "2026-11-01")
try:
    DEMO_AS_OF_DATE = date.fromisoformat(DEMO_AS_OF_DATE_STR)
except Exception:
    DEMO_AS_OF_DATE = date(2026, 11, 1)
