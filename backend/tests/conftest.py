import os
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")

from backend import create_app
from backend.db.db_connection import Base
import backend.db.models


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    test_session = sessionmaker(bind=connection)()

    yield test_session

    test_session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def app(engine, session):
    application = create_app()
    application.config.update({"TESTING": True, "DATABASE_URI": str(engine.url)})
    with patch("backend.auth.routes.session", session):
        yield application


@pytest.fixture()
def client(app):
    return app.test_client()
