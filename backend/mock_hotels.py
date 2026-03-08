from faker import Faker
from sqlalchemy import insert, select
from models import Hotel, HotelRoom, RoomDate
from datetime import date, timedelta

fake = Faker()

Faker.seed(0)

START_DATE = date(2025, 3, 23) # hardcoded start date (midterm demo) so we have the same booking dates

def mock_hotels(conn):
    for _ in range(50):
        insert_hotel_stmt = insert(Hotel).values(
            name = fake.company(),
            price_per_night = fake.pydecimal(left_digits=4, right_digits=2, positive=True, min_value=50, max_value=500),
            city = fake.city(),
            address = fake.unique.street_address(),
            rating=0
        )
        conn.execute(insert_hotel_stmt)

def mock_hotel_rooms(conn):
    hotels_result = conn.execute(select(Hotel.id))
    all_hotels = hotels_result.fetchall()

    for hotel in all_hotels:
        for room_number in range(1, fake.random_int(min=6, max=25)): # 5-25 rooms per hotel
            insert_hotel_room_stmt = insert(HotelRoom).values(
                hotel = hotel.id,
                room = room_number
            )
            conn.execute(insert_hotel_room_stmt)

def mock_room_dates(conn):
    hotel_rooms_result = conn.execute(select(HotelRoom.id))
    all_hotel_rooms = hotel_rooms_result.fetchall()
    all_dates = [START_DATE + timedelta(days=i) for i in range(180)] # 6 months of available booking dates from start date

    for room in all_hotel_rooms:
        for d in all_dates: 
            insert_room_date_stmt = insert(RoomDate).values(
                room = room.id,
                date = d,
                is_available = True
            )
            conn.execute(insert_room_date_stmt)