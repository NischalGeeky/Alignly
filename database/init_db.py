import logging
import sys
from database.connection import Base, engine
import database.models  # ensure models are registered with Base.metadata
from utils.logging_config import configure_logging

logger = configure_logging()

def init_db() -> None:
    """Initialize all tables defined in models on the configured database."""
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        print("Success: All database tables created successfully.")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        print(f"Error: Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    init_db()

# Provide a callable for tests expecting a main function
def main() -> None:
    """Entry point used by tests to initialize the database tables."""
    init_db()
    init_db()
