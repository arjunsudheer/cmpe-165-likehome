import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")

from backend.db.db_connection import Base  # pylint: disable=wrong-import-position
import backend.db.models  # noqa: F401  # pylint: disable=wrong-import-position,unused-import


@pytest.fixture(scope="session")
def engine():
    """Create a shared in-memory SQLite engine for the test session."""
    eng = create_engine("sqlite:///:memory:")

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # pylint: disable=unused-argument
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def session(engine):  # pylint: disable=redefined-outer-name
    """Provide a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    test_session = sessionmaker(bind=connection)()

    yield test_session

    test_session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
