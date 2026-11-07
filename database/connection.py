from contextlib import contextmanager
from typing import Generator
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
import config

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Set check_same_thread=False when using SQLite
connect_args = {}
if config.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        config.DATABASE_URL,
        connect_args=connect_args,
        echo=False,
        future=True,
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        future=True,
    )
except Exception as e:
    logger.error("Failed to initialize database engine: %s", e)
    raise

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("Database session rollback due to exception: %s", e)
        raise
    finally:
        session.close()
