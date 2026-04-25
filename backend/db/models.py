import enum

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime,
    Enum, ForeignKey, Integer, Numeric, String, func, JSON
)
from backend.db.db_connection import Base


class RoomType(enum.Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUAD = "QUAD"


class Status(enum.Enum):
    INPROGRESS = "INPROGRESS"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class CouponType(enum.Enum):
    FREESTAY = "FREESTAY"

class CouponStatus(enum.Enum):
    REDEEMABLE = "REDEEMABLE"
    REDEEMED = "REDEEMED"
    EXPIRED = "EXPIRED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), CheckConstraint("email = lower(email)"), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    points = Column(Integer, nullable=False, default=0)
    send_reminder_email = Column(Boolean, default=True)


class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price_per_night = Column(Numeric(10, 2), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(100), unique=True, nullable=False)
    rating = Column(Numeric, CheckConstraint("rating >= 0 AND rating <= 5"), default=0)


class HotelRoom(Base):
    __tablename__ = "hotel_rooms"
    id = Column(Integer, primary_key=True)
    hotel = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room = Column(Integer, nullable=False)
    # native_enum=False stores as VARCHAR — no PostgreSQL type sync needed
    room_type = Column(Enum(RoomType, native_enum=False), nullable=False)


class HotelPhoto(Base):
    __tablename__ = "hotel_photos"
    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    url = Column(String(255), nullable=False)
    alt_text = Column(String(255), nullable=False, default="Hotel photo")


class HotelAmenity(Base):
    __tablename__ = "hotel_amenities"
    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    name = Column(String(100), nullable=False)


class CancellationPolicy(Base):
    __tablename__ = "cancellation_policies"
    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, unique=True)
    deadline_hours = Column(Integer, nullable=False, default=48)
    fee_percent = Column(Numeric(5, 2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    booking_number = Column(String(12), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    user = Column(Integer, ForeignKey("users.id"), nullable=False)
    room = Column(Integer, ForeignKey("hotel_rooms.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    # native_enum=False avoids the PostgreSQL enum type going out of sync
    status = Column(Enum(Status, native_enum=False), default=Status.CONFIRMED)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    reminder_email_sent = Column(Boolean, default=False)
    reminder_notification_created = Column(Boolean, default=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("users.id"), nullable=False)
    hotel = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    title = Column(String(20), default="No title")
    content = Column(String(255), default="No content")
    rating = Column(Integer, CheckConstraint("rating >= 1 AND rating <= 5"), nullable=False)


class PointsTransaction(Base):
    __tablename__ = "points_transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    points = Column(Integer, nullable=False)
    log = Column(String(100), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now())


class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    coupon_type = Column(Enum(CouponType, native_enum=False), nullable=False)
    value_in_points = Column(Integer, nullable=False)
    status = Column(Enum(CouponStatus, native_enum=False), default=CouponStatus.REDEEMABLE)
    expires_at = Column(DateTime)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    destination = Column(String(100), nullable=False)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    guests = Column(Integer, nullable=False)
    filters = Column(JSON)
    sorting = Column(JSON)
    recorded_at = Column(DateTime, server_default=func.now())
