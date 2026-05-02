from datetime import datetime, timezone, timedelta
from sqlalchemy import update, insert, select
from sqlalchemy.orm import Session
from backend.db.db_connection import engine
from backend.db.queries import booking_points_redeemed_total
from backend.db.models import (
    Booking,
    Status,
    PointsTransaction,
    User,
    Coupon,
    CouponType,
    CouponStatus,
    Notification
)
from backend.utils.email import send_email

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
                if booking_points_redeemed_total(session, booking.id) > 0:
                    continue
            session.commit()

        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to update bookings: {e}") from e

def create_booking_reminders():
    with Session(engine) as session:
        try:
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
            
            # Find bookings that start tomorrow, are confirmed, and haven't had a notification created
            # Join with User to check their preference
            # Use with_for_update(skip_locked=True) to prevent multiple workers from processing the same booking
            eligible_records = session.execute(
                select(Booking, User)
                .join(User, Booking.user == User.id)
                .where(
                    Booking.start_date == tomorrow,
                    Booking.status == Status.CONFIRMED,
                    Booking.reminder_notification_created.is_(False),
                    User.send_reminder_email.is_(True)
                )
                .with_for_update(of=Booking, skip_locked=True)
            ).all()

            for booking, user in eligible_records:
                message = f"Reminder: Your upcoming stay for booking {booking.booking_number} starts on {booking.start_date}."
                
                try:
                    # Create Notification
                    session.execute(
                        insert(Notification)
                        .values(
                            user_id=user.id,
                            message=message,
                            is_read=False,
                            created_at=datetime.now()
                        )
                    )
                    
                    # Mark reminder notification as created
                    session.execute(
                        update(Booking)
                        .where(Booking.id == booking.id)
                        .values(reminder_notification_created=True)
                    )
                    session.flush()

                    # Send Email Notification
                    subject = "Upcoming Stay Reminder - LikeHome"
                    send_email(user.email, subject, message)
                except Exception as e: # pylint: disable=broad-exception-caught
                    print(f"Error creating notification for {user.email}: {e}")
                    
            session.commit()
        except Exception as e: # pylint: disable=broad-exception-caught
            session.rollback()
            raise RuntimeError(f"Failed to create booking reminders: {e}") from e
