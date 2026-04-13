from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session

from backend.db.db_connection import engine
from backend.db.models import User, PointsTransaction, Booking, Status, HotelRoom
from backend.extensions import bcrypt


def get_reward_points(user_id):
    with Session(engine) as session:
        stmt = select(User.points).where(User.id == user_id)
        result = session.execute(stmt)
        return result.scalar_one()


def get_points_history(user_id):
    with Session(engine) as session:
        stmt = (
            select(PointsTransaction)
            .where(PointsTransaction.user_id == user_id)
            .order_by(PointsTransaction.recorded_at.desc())
        )
        return session.execute(stmt).scalars().all()


def verify_login(email, password):
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        user = session.execute(stmt).scalar_one_or_none()
        if user is None:
            return {"success": False, "message": "Email not found"}
        if not bcrypt.check_password_hash(user.password, password):
            return {"success": False, "message": "Incorrect password"}
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user.id
        }


def room_availability(start_date, end_date, hotel_id):
    with Session(engine) as session:
        overlapping = (
            select(Booking.id)
            .where(
                Booking.room == HotelRoom.id,
                Booking.start_date < end_date,
                Booking.end_date > start_date,
                or_(
                    Booking.status == Status.INPROGRESS,
                    Booking.status == Status.CONFIRMED,
                ),
            )
        )
        stmt = select(HotelRoom.id).where(HotelRoom.hotel == hotel_id, ~exists(overlapping))
        result = session.execute(stmt)
        return result.scalars().all()


def get_overlapping_booking_dates(user_id, start_date, end_date):
    with Session(engine) as session:
        stmt = select(
            Booking.id, Booking.title, Booking.start_date, Booking.end_date
        ).where(
            and_(
                Booking.user == user_id,
                Booking.status != Status.CANCELLED,
                start_date <= Booking.end_date,
                end_date >= Booking.start_date,
            )
        )
        return session.execute(stmt).all()
