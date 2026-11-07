import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from database.connection import Base
import database.models  # load all models into Base.metadata

@pytest.fixture(scope="session")
def test_engine():
    """Create an isolated in-memory SQLite engine with foreign key support enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Enable SQLite foreign key constraint enforcement
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide a transactional session for each test that rolls back changes."""
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, future=True)
    session = SessionLocal()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
