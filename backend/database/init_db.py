from database.db_connection import engine, Base
from backend.database.mock_hotels import mock_hotels, mock_hotel_rooms
from sqlalchemy import select
from models import Hotel

def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)
    with engine.begin() as conn:
        hotel = conn.execute(select(Hotel)).first()
        if hotel is None:
            mock_hotels(conn)
            mock_hotel_rooms(conn)

if __name__ == "__main__":
    init_tables_and_data()