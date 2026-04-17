"""
Pure helper functions for reservation logic.
Kept separate from routes.py so tests can import them without
triggering Flask/SQLAlchemy app-context setup.
"""
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import and_, select

from backend.db.models import Booking, CancellationPolicy, HotelRoom, Status


DEFAULT_CANCELLATION_WINDOW_HOURS = 48
DEFAULT_CANCELLATION_FEE_PERCENT = Decimal("0.00")


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


def get_cancellation_policy(db, booking: Booking) -> dict:
    room = db.get(HotelRoom, booking.room)
    if room is None:
        return {
            "policy_hours": DEFAULT_CANCELLATION_WINDOW_HOURS,
            "fee_percent": DEFAULT_CANCELLATION_FEE_PERCENT,
        }

    policy = db.execute(
        select(CancellationPolicy).where(
            and_(
                CancellationPolicy.hotel_id == room.hotel,
                CancellationPolicy.active.is_(True),
            )
        )
    ).scalar_one_or_none()

    if policy is None:
        return {
            "policy_hours": DEFAULT_CANCELLATION_WINDOW_HOURS,
            "fee_percent": DEFAULT_CANCELLATION_FEE_PERCENT,
        }

    return {
        "policy_hours": int(policy.deadline_hours),
        "fee_percent": Decimal(str(policy.fee_percent)).quantize(Decimal("0.01")),
    }


def get_cancellation_details(
    db,
    booking: Booking,
    now: datetime | None = None,
) -> dict:
    """
    Calculate whether a booking can be cancelled and the refund summary
    using the active hotel cancellation policy.
    """
    if now is None:
        now = datetime.now()

    policy = get_cancellation_policy(db, booking)
    policy_hours = policy["policy_hours"]
    fee_percent = policy["fee_percent"]

    check_in_at = datetime.combine(booking.start_date, time.min)
    cutoff_at = check_in_at - timedelta(hours=policy_hours)
    total_price = Decimal(str(booking.total_price)).quantize(Decimal("0.01"))
    fee_amount = (total_price * fee_percent / Decimal("100")).quantize(Decimal("0.01"))
    refund_amount = max(Decimal("0.00"), total_price - fee_amount)

    return {
        "allowed": now <= cutoff_at,
        "policy_hours": policy_hours,
        "fee_percent": fee_percent,
        "check_in_at": check_in_at,
        "cutoff_at": cutoff_at,
        "fee_amount": fee_amount,
        "refund_amount": refund_amount,
    }
