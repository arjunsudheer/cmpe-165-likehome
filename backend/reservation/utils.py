"""
Pure helper functions for reservation logic.
Kept separate from routes.py so tests can import them without
triggering Flask/SQLAlchemy app-context setup.
"""
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import and_, select

from backend.db.models import Booking, Status


CANCELLATION_WINDOW_HOURS = 48
CANCELLATION_FEE = Decimal("0.00")


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


def get_cancellation_details(
    booking: Booking,
    now: datetime | None = None,
    fee: Decimal = CANCELLATION_FEE,
) -> dict:
    """
    Calculate whether a booking can be cancelled and the refund summary.

    Because bookings only store a check-in date, we treat the start of the
    check-in day as the cutoff anchor for the 48-hour policy.
    """
    if now is None:
        now = datetime.now()

    check_in_at = datetime.combine(booking.start_date, time.min)
    cutoff_at = check_in_at - timedelta(hours=CANCELLATION_WINDOW_HOURS)
    fee_amount = Decimal(str(fee)).quantize(Decimal("0.01"))
    total_price = Decimal(str(booking.total_price)).quantize(Decimal("0.01"))
    refund_amount = max(Decimal("0.00"), total_price - fee_amount)

    return {
        "allowed": now <= cutoff_at,
        "policy_hours": CANCELLATION_WINDOW_HOURS,
        "check_in_at": check_in_at,
        "cutoff_at": cutoff_at,
        "fee_amount": fee_amount,
        "refund_amount": refund_amount,
    }
