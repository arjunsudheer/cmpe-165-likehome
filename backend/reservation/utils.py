"""
Pure helper functions for reservation logic.
Kept separate from routes.py so tests can import them without
triggering Flask/SQLAlchemy app-context setup.
"""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, select

from backend.db.models import Booking, Status


def generate_booking_number() -> str:
    """Return a unique booking reference in the format LH-XXXXXXXX."""
    return "LH-" + uuid.uuid4().hex[:8].upper()


def calculate_total_price(
    price_per_night: Decimal, start_date: date, end_date: date
) -> Decimal:
    """Return price_per_night × number of nights as a Decimal."""
    nights = (end_date - start_date).days
    return Decimal(str(price_per_night)) * nights


def check_room_availability(
    db,
    room_id: int,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
) -> list:
    """
    Return all active Booking rows that overlap the requested date window
    for the given room.  Pass exclude_booking_id to ignore a booking being
    modified (e.g. during a reschedule).
    """
    stmt = select(Booking).where(
        and_(
            Booking.room == room_id,
            Booking.status != Status.CANCELLED,
            Booking.start_date < end_date,
            Booking.end_date > start_date,
        )
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(Booking.id != exclude_booking_id)
    return db.execute(stmt).scalars().all()
