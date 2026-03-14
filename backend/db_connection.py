from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import DeclarativeBase
from mock_hotels import mock_hotels, mock_hotel_rooms
import os
from dotenv import load_dotenv
from models import Hotel
import models

load_dotenv()

DATABASE_URL= f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

class Base(DeclarativeBase):
    pass

def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)
    with engine.begin() as conn:
        hotel = conn.execute(select(Hotel)).first()
        if hotel is None:
            mock_hotels(conn)
            mock_hotel_rooms(conn)

if __name__ == "__main__":
    init_tables_and_data()