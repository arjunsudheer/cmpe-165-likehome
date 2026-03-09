from db_connection import engine, Base
from mock_hotels import mock_hotels, mock_hotel_rooms
import models

def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)
    with engine.connect() as conn:
        mock_hotels(conn)
        mock_hotel_rooms(conn)
        conn.commit()

if __name__ == "__main__":
    init_tables_and_data()