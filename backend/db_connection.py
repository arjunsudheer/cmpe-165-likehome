from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv
import models

load_dotenv()

DATABASE_URL= f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

class Base(DeclarativeBase):
    pass

def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)

if __name__ == "__main__":
    init_tables_and_data()