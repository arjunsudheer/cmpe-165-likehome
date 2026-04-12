from datetime import datetime, timezone
from sqlalchemy import update, insert, select
from sqlalchemy.orm import Session
from backend.db.db_connection import engine
from backend.db.models import (
    Booking,
    Status,
    PointsTransaction,
    User,
    Coupon,
    CouponType,
    CouponStatus
)

POINTS_PER_DOLLAR = 10
FREE_STAY_THRESHOLD = 100000

def expire_bookings():
    with Session(engine) as session:
        session.execute(
            update(Booking)
            .where(
                Booking.status == Status.INPROGRESS, Booking.expires_at < datetime.now()
            )
            .values(status=Status.CANCELLED)
        )
        session.commit()

def complete_bookings_and_earn_points():
    with Session(engine) as session:
        try:
            completed_bookings = session.scalars(
                select(Booking)
                .where(
                    Booking.end_date < datetime.now(timezone.utc).date(),
                    Booking.status==Status.CONFIRMED
                )
            ).all()

            booking_ids = [b.id for b in completed_bookings]

            session.execute(
                update(Booking)
                .where(Booking.id.in_(booking_ids))
                .values(status=Status.COMPLETED)
            )

            for booking in completed_bookings:
                points_earned = int(float(booking.total_price) * POINTS_PER_DOLLAR)
                session.execute(
                    update(User)
                    .where(User.id == booking.user)
                    .values(points = User.points + points_earned)
                )
                session.flush()
                check_points_for_free_stay(user_id=booking.user, session=session)
                session.execute(
                    insert(PointsTransaction)
                    .values(
                        user_id = booking.user,
                        booking_id = booking.id,
                        points = points_earned,
                        log = f"Earned {points_earned} points on booking #{booking.id}",
                        recorded_at = datetime.now()
                    )
                )
            session.commit()

        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to update bookings: {e}") from e

def check_points_for_free_stay(user_id, session):
    user = session.scalars(
        select(User)
        .where(User.id == user_id, User.points >= FREE_STAY_THRESHOLD)
    ).one_or_none()
    if user:
        # just allows one free stay coupon at once per user
        existing_coupon = session.scalars(
            select(Coupon)
            .where(
                Coupon.user_id==user_id,
                Coupon.coupon_type==CouponType.FREESTAY,
                Coupon.status==CouponStatus.REDEEMABLE
            )
        ).first()
        if not existing_coupon:
            session.execute(
                insert(Coupon)
                .values(
                    user_id=user_id,
                    coupon_type=CouponType.FREESTAY,
                    value_in_points=FREE_STAY_THRESHOLD
                )
            )
