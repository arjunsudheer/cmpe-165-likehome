from db_connection import Base
import enum
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, func, ForeignKey, CheckConstraint, Enum

class RoomType(enum.Enum):
    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    QUAD = "QUAD"

class Status(enum.Enum):
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False) # is longer to store w/ hashing
    points = Column(Integer, nullable=False, default=0) # ALTER TABLE users ADD COLUMN points INTEGER NOT NULL DEFAULT 0; (if you init db before this was here)

class Hotel(Base):
    __tablename__ = "hotels"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price_per_night = Column(Numeric(10, 2), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(100), unique=True, nullable=False)
    rating = Column(Numeric, CheckConstraint('rating >= 0 AND rating <= 5'), default=0)

class HotelRoom(Base):
    __tablename__ = "hotel_rooms"
    id = Column(Integer, primary_key=True)
    hotel = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    room = Column(Integer, nullable=False)
    room_type = Column(Enum(RoomType), nullable=False)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    user = Column(Integer, ForeignKey("users.id"), nullable=False)
    room = Column(Integer, ForeignKey("hotel_rooms.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(Status), default=Status.CONFIRMED)
    created_at = Column(DateTime, server_default = func.now())

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user = Column(Integer, ForeignKey("users.id"), nullable=False)
    hotel = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    title = Column(String(20), default="No title")
    content = Column(String(255), default="No content")
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 5'), nullable=False)

class PointsTransaction(Base):
    __tablename__ = "points_transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    points = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, server_default = func.now())