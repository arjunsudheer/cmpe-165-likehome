from sqlalchemy import select

from backend.db.db_connection import Base, engine
from backend.db.models import (
    CancellationPolicy,
    Hotel,
    HotelAmenity,
    HotelPhoto,
    HotelRoom,
    Review,
    User,
)
from backend.db.mock_hotels import (
    mock_hotel_amenities,
    mock_hotel_photos,
    mock_hotel_rooms,
    mock_hotels,
    mock_review_users,
    mock_reviews,
)
from backend.db.schema_patches import (
    ensure_points_transactions_log_column,
    ensure_reminder_email_columns,
    ensure_notifications_table,
)
from backend.search.routes import refresh_hotel_rating

def mock_cancellation_policies(conn):
    hotel_ids = [row.id for row in conn.execute(select(Hotel.id)).fetchall()]
    for hotel_id in hotel_ids:
        existing = conn.execute(
            select(CancellationPolicy).where(CancellationPolicy.hotel_id == hotel_id)
        ).first()
        if existing is None:
            conn.execute(
                CancellationPolicy.__table__.insert().values(
                    hotel_id=hotel_id,
                    deadline_hours=48,
                    fee_percent=0,
                    active=True,
                )
            )


def init_tables_and_data():
    Base.metadata.create_all(engine, checkfirst=True)
    ensure_points_transactions_log_column()
    ensure_reminder_email_columns()
    ensure_notifications_table()
    with engine.begin() as conn:
        hotel = conn.execute(select(Hotel)).first()
        if hotel is None:
            mock_hotels(conn)

        hotel_room = conn.execute(select(HotelRoom)).first()
        if hotel_room is None:
            mock_hotel_rooms(conn)

        hotel_photo = conn.execute(select(HotelPhoto)).first()
        if hotel_photo is None:
            mock_hotel_photos(conn)

        hotel_amenity = conn.execute(select(HotelAmenity)).first()
        if hotel_amenity is None:
            mock_hotel_amenities(conn)

        policy = conn.execute(select(CancellationPolicy)).first()
        if policy is None:
            mock_cancellation_policies(conn)
        
        user = conn.execute(select(User)).first()
        if user is None:
            mock_review_users(conn)

        review = conn.execute(select(Review)).first()
        if review is None:
            mock_reviews(conn)

    with engine.begin() as conn:
        hotel_ids = [row.id for row in conn.execute(select(Hotel.id)).fetchall()]

    for hotel_id in hotel_ids:
        refresh_hotel_rating(hotel_id)


if __name__ == "__main__":
    init_tables_and_data()
