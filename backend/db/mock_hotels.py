from faker import Faker
from sqlalchemy import insert, select
from backend.db.models import Hotel, HotelRoom, RoomType

fake = Faker()

Faker.seed(0)


def mock_hotels(conn):
    for _ in range(50):
        insert_hotel_stmt = insert(Hotel).values(
            name=fake.company(),
            price_per_night=fake.pydecimal(
                left_digits=4,
                right_digits=2,
                positive=True,
                min_value=50,
                max_value=500,
            ),
            city=fake.city(),
            address=fake.unique.street_address(),
            rating=0,
        )
        conn.execute(insert_hotel_stmt)


def mock_hotel_rooms(conn):
    hotels_result = conn.execute(select(Hotel.id))
    all_hotels = hotels_result.fetchall()

    for hotel in all_hotels:
        for room_number in range(
            1, fake.random_int(min=6, max=25)
        ):  # 5-25 rooms per hotel
            insert_hotel_room_stmt = insert(HotelRoom).values(
                hotel=hotel.id,
                room=room_number,
                room_type=fake.random_element([e.value for e in RoomType]),
            )
            conn.execute(insert_hotel_room_stmt)
