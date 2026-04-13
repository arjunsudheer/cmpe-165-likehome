import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
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


def _make_typed_room(session, hotel, room_no, room_type):
    r = HotelRoom(hotel=hotel.id, room=room_no, room_type=room_type)
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


@pytest.fixture()
def reservation_client(client, session):
    bind = session.get_bind()
    with patch("backend.reservation.routes.engine", bind), patch(
        "backend.db.queries.engine", bind
    ):
        yield client


def _auth_headers(client, email="modify@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "name": "Modify Tester",
            "email": email,
            "password": "password123",
        },
    )
    assert response.status_code == 201
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


class TestModifyReservation:

    def test_modify_booking_dates_success(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "date-change@example.com")
        user = session.query(User).filter_by(email="date-change@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 101, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date(2027, 1, 10),
            date(2027, 1, 12),
            price="200.00",
        )

        response = reservation_client.patch(
            f"/reservations/{booking.id}",
            json={
                "title": "Updated Test Stay",
                "room": room.id,
                "start_date": "2027-01-15",
                "end_date": "2027-01-18",
            },
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["message"] == "Booking updated"
        assert payload["booking"]["start_date"] == "2027-01-15"
        assert payload["booking"]["end_date"] == "2027-01-18"

        session.expire_all()
        updated = session.get(Booking, booking.id)
        assert updated.start_date == date(2027, 1, 15)
        assert updated.end_date == date(2027, 1, 18)

    def test_modify_booking_room_success(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "room-change@example.com")
        user = session.query(User).filter_by(email="room-change@example.com").one()
        hotel = _make_hotel(session)
        original_room = _make_typed_room(session, hotel, 101, RoomType.DOUBLE)
        new_room = _make_typed_room(session, hotel, 102, RoomType.TRIPLE)
        booking = _make_booking(
            session,
            user,
            original_room,
            date(2027, 2, 1),
            date(2027, 2, 3),
            price="200.00",
        )

        response = reservation_client.patch(
            f"/reservations/{booking.id}",
            json={
                "title": "Updated Room Test",
                "room": new_room.id,
                "start_date": "2027-02-01",
                "end_date": "2027-02-03",
            },
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["booking"]["id"] == booking.id

        session.expire_all()
        updated = session.get(Booking, booking.id)
        assert updated.room == new_room.id

    def test_modify_booking_recalculates_total_price(
        self, reservation_client, session
    ):
        headers = _auth_headers(
            reservation_client, "cost-recalculation@example.com"
        )
        user = session.query(User).filter_by(
            email="cost-recalculation@example.com"
        ).one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 101, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date(2027, 3, 10),
            date(2027, 3, 12),
            price="200.00",
        )

        response = reservation_client.patch(
            f"/reservations/{booking.id}",
            json={
                "title": "Updated Price Test",
                "room": room.id,
                "start_date": "2027-03-10",
                "end_date": "2027-03-14",
            },
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert Decimal(payload["booking"]["total_price"]) == Decimal("400.00")

        session.expire_all()
        updated = session.get(Booking, booking.id)
        assert updated.total_price == Decimal("400.00")

class TestRedemptionAccuracy:

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_redeem_deducts_correct_points(self, reservation_client, session):
        token, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test.com"
        )
        before = user.points
        reservation_client.post(
            "/rewards/redeem",
            json={"points": 100, "booking_id": booking.id},
            headers=self._auth(token),
        )
        session.expire_all()
        assert session.get(User, user.id).points == before - 100

    def test_redeem_cannot_exceed_booking_total(self, reservation_client, session):
        token, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test.com"
        )
        user.points = 99999
        session.flush()
        excess_points = int(float(booking.total_price) * 100) + 500
        response = reservation_client.post(
            "/rewards/redeem",
            json={"points": excess_points, "booking_id": booking.id},
            headers=self._auth(token),
        )
        assert response.status_code == 400

    def test_points_not_deducted_on_failed_redemption(self, reservation_client, session):
        token, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test.com"
        )
        before = user.points
        reservation_client.post(
            "/rewards/redeem",
            json={"points": -50, "booking_id": booking.id},
            headers=self._auth(token),
        )
        session.expire_all()
        assert session.get(User, user.id).points == before

    def test_partial_redeem_leaves_correct_remainder(self, reservation_client, session):
        token, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test.com"
        )
        points_to_use = 200
        balance_before = user.points
        total_before = booking.total_price
        reservation_client.post(
            "/rewards/redeem",
            json={"points": points_to_use, "booking_id": booking.id},
            headers=self._auth(token),
        )
        session.expire_all()
        updated_user = session.get(User, user.id)
        updated_booking = session.get(Booking, booking.id)
        assert updated_user.points == balance_before - points_to_use
        assert updated_booking.total_price == total_before - Decimal("2.00")