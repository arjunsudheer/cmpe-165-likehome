from pathlib import Path

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
import os
from dotenv import load_dotenv

# Repo root .env — do not override existing env (Docker / CI already set DATABASE_URL)
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=False)

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip() or None
if not DATABASE_URL and Path("/.dockerenv").exists():
    # Backend container on Compose network (matches docker-compose.yml db service)
    DATABASE_URL = "postgresql://likehome:likehome@db:5432/likehome"
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to the project root .env file, or run the app via docker compose."
    )

engine = create_engine(DATABASE_URL)
metadata = MetaData()


class Base(DeclarativeBase):
    pass


SessionLocal = scoped_session(sessionmaker(bind=engine))
session = SessionLocal()
