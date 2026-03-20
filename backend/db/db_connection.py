from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker, scoped_session
import os
from dotenv import load_dotenv

load_dotenv()

print(repr(os.getenv("DB_PORT")))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
metadata = MetaData()


class Base(DeclarativeBase):
    pass


SessionLocal = scoped_session(sessionmaker(bind=engine))
session = SessionLocal()
