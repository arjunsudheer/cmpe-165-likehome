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
    Booking,
    PointsTransaction,
    Coupon,
)
from backend.db.schema_patches import (
    ensure_points_transactions_log_column,
    ensure_reminder_email_columns,
    ensure_notifications_table,
)

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


def init_tables():
    Base.metadata.create_all(engine, checkfirst=True)
    ensure_points_transactions_log_column()
    ensure_reminder_email_columns()
    ensure_notifications_table()


if __name__ == "__main__":
    init_tables()
