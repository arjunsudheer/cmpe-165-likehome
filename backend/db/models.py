import enum

from sqlalchemy import (
    CheckConstraint, Column, Date, DateTime,
    Enum, ForeignKey, Integer, Numeric, String, func,
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


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), CheckConstraint("email = lower(email)"), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    points = Column(Integer, nullable=False, default=0)


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
    recorded_at = Column(DateTime, server_default=func.now())
