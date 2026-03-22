import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from backend import create_app

# set fallback env vars so db_connection.py doesn't crash on import
for var, val in [
    ("DB_USERNAME", "test"),
    ("DB_PASSWORD", "test"),
    ("DB_HOST", "localhost"),
    ("DB_PORT", "5432"),
    ("DB_NAME", "test"),
    ("DATABASE_URL", "sqlite:///:memory:"),
]:
    os.environ.setdefault(var, val)

from backend.db.db_connection import Base
import backend.db.models


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
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
    Session = sessionmaker(bind=connection)
    sess = Session()

    yield sess

    sess.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def app(engine, session):
    app = create_app()
    app.config.update({"TESTING": True, "DATABASE_URI": str(engine.url)})
    with patch("backend.auth.routes.session", session):
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()
