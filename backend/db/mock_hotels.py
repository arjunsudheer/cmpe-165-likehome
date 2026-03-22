import json
from pathlib import Path

from faker import Faker
from sqlalchemy import insert, select

from backend.db.models import (
    Hotel,
    HotelAmenity,
    HotelPhoto,
    HotelRoom,
    Review,
    RoomType,
    User,
)

fake = Faker()

Faker.seed(0)

SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "hotel_details.json"


def load_hotel_detail_seed_data():
    with SEED_FILE.open(encoding="utf-8") as seed_file:
        return json.load(seed_file)


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
        for room_number in range(1, fake.random_int(min=6, max=25)):
            insert_hotel_room_stmt = insert(HotelRoom).values(
                hotel=hotel.id,
                room=room_number,
                room_type=fake.random_element([e.value for e in RoomType]),
            )
            conn.execute(insert_hotel_room_stmt)


def mock_hotel_photos(conn):
    hotels_result = conn.execute(select(Hotel.id))
    all_hotels = hotels_result.fetchall()
    seed_data = load_hotel_detail_seed_data()
    photo_sets = seed_data["photo_sets"]

    for hotel in all_hotels:
        photo_set = photo_sets[(hotel.id - 1) % len(photo_sets)]
        for photo in photo_set:
            conn.execute(
                insert(HotelPhoto).values(
                    hotel_id=hotel.id,
                    url=photo["url"],
                    alt_text=photo["alt_text"],
                )
            )


def mock_hotel_amenities(conn):
    hotels_result = conn.execute(select(Hotel.id))
    all_hotels = hotels_result.fetchall()
    seed_data = load_hotel_detail_seed_data()
    amenity_sets = seed_data["amenity_sets"]

    for hotel in all_hotels:
        amenity_set = amenity_sets[(hotel.id - 1) % len(amenity_sets)]
        for amenity_name in amenity_set:
            conn.execute(
                insert(HotelAmenity).values(
                    hotel_id=hotel.id,
                    name=amenity_name,
                )
            )


def mock_review_users(conn):
    users_result = conn.execute(select(User.id)).first()
    if users_result is not None:
        return

    for index in range(1, 6):
        conn.execute(
            insert(User).values(
                email=f"reviewer{index}@example.com",
                password="seeded-password",
            )
        )


def mock_reviews(conn):
    hotels_result = conn.execute(select(Hotel.id))
    user_ids = [row.id for row in conn.execute(select(User.id)).fetchall()]
    if not user_ids:
        return

    for index, hotel in enumerate(hotels_result.fetchall(), start=1):
        for review_offset in range(2):
            user_id = user_ids[(index + review_offset - 1) % len(user_ids)]
            conn.execute(
                insert(Review).values(
                    user=user_id,
                    hotel=hotel.id,
                    title=f"Guest review {review_offset + 1}",
                    content=f"Comfortable stay at hotel {hotel.id}.",
                    rating=4 if review_offset == 0 else 5,
                )
            )
