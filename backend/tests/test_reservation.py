import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from backend.db.models import User, Hotel, HotelRoom, Booking, RoomType, Status
from backend.reservation.utils import (
    generate_booking_number,
    check_room_availability,
    calculate_total_price,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_user(session, email="guest@example.com"):
    u = User(email=email, password="hashed")
    session.add(u)
    session.flush()
    return u


def _make_hotel(session):
    h = Hotel(
        name="Test Hotel",
        price_per_night=Decimal("100.00"),
        city="San Jose",
        address="1 Main St",
    )
    session.add(h)
    session.flush()
    return h


def _make_room(session, hotel):
    r = HotelRoom(hotel=hotel.id, room=101, room_type=RoomType.DOUBLE)
    session.add(r)
    session.flush()
    return r


def _make_booking(session, user, room, start, end, price="200.00"):
    b = Booking(
        booking_number=generate_booking_number(),
        title="Test Stay",
        user=user.id,
        room=room.id,
        start_date=start,
        end_date=end,
        total_price=Decimal(price),
        status=Status.CONFIRMED,
    )
    session.add(b)
    session.flush()
    return b


# ── Booking number generation ─────────────────────────────────────────────────


class TestBookingNumber:

    def test_format(self):
        num = generate_booking_number()
        assert num.startswith("LH-")
        assert len(num) == 11

    def test_unique(self):
        numbers = {generate_booking_number() for _ in range(100)}
        assert len(numbers) == 100


# ── Price calculation ─────────────────────────────────────────────────────────


class TestPriceCalculation:

    def test_single_night(self):
        assert calculate_total_price(
            Decimal("100.00"), date(2026, 4, 1), date(2026, 4, 2)
        ) == Decimal("100.00")

    def test_multiple_nights(self):
        assert calculate_total_price(
            Decimal("149.99"), date(2026, 4, 1), date(2026, 4, 4)
        ) == Decimal("449.97")


# ── Room availability ─────────────────────────────────────────────────────────


class TestRoomAvailability:

    def test_no_conflict(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room, date(2026, 4, 1), date(2026, 4, 3))

        conflicts = check_room_availability(
            session, room.id, date(2026, 4, 5), date(2026, 4, 7)
        )
        assert len(conflicts) == 0

    def test_overlap_detected(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room, date(2026, 4, 1), date(2026, 4, 5))

        conflicts = check_room_availability(
            session, room.id, date(2026, 4, 3), date(2026, 4, 7)
        )
        assert len(conflicts) == 1

    def test_adjacent_dates_no_conflict(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room, date(2026, 4, 1), date(2026, 4, 3))

        # Check-out on the same day as a new check-in is not a conflict
        conflicts = check_room_availability(
            session, room.id, date(2026, 4, 3), date(2026, 4, 5)
        )
        assert len(conflicts) == 0

    def test_cancelled_booking_ignored(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        b = _make_booking(session, user, room, date(2026, 4, 1), date(2026, 4, 5))
        b.status = Status.CANCELLED
        session.flush()

        conflicts = check_room_availability(
            session, room.id, date(2026, 4, 2), date(2026, 4, 4)
        )
        assert len(conflicts) == 0


# ── Booking model constraints ─────────────────────────────────────────────────


class TestBookingModel:

    def test_create_booking(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        b = _make_booking(session, user, room, date(2026, 5, 1), date(2026, 5, 3))

        assert b.id is not None
        assert b.booking_number.startswith("LH-")
        assert b.status == Status.CONFIRMED

    def test_booking_number_unique(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        b1 = _make_booking(session, user, room, date(2026, 5, 1), date(2026, 5, 2))

        b2 = Booking(
            booking_number=b1.booking_number,
            title="Dup",
            user=user.id,
            room=room.id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 2),
            total_price=Decimal("100.00"),
        )
        session.add(b2)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_cancel_booking(self, session):
        user = _make_user(session)
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        b = _make_booking(session, user, room, date(2026, 5, 1), date(2026, 5, 3))

        b.status = Status.CANCELLED
        session.flush()
        assert b.status == Status.CANCELLED
