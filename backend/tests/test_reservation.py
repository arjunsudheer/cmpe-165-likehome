import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from backend.db.models import (
    Booking, CancellationPolicy, Hotel, HotelRoom, PointsTransaction,
    RoomType, Status, User,
)
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


def _make_cancellation_policy(
    session,
    hotel,
    deadline_hours=48,
    fee_percent="0.00",
    active=True,
):
    policy = CancellationPolicy(
        hotel_id=hotel.id,
        deadline_hours=deadline_hours,
        fee_percent=Decimal(fee_percent),
        active=active,
    )
    session.add(policy)
    session.flush()
    return policy


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
    ), patch(
        "backend.rewards.routes.engine", bind
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


class TestListBookings:

    def test_list_bookings_includes_inprogress_bookings(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "pending-list@example.com")
        user = session.query(User).filter_by(email="pending-list@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 111, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date(2027, 4, 10),
            date(2027, 4, 12),
        )
        booking.status = Status.INPROGRESS
        session.flush()

        response = reservation_client.get("/reservations/", headers=headers)

        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload) == 1
        assert payload[0]["id"] == booking.id
        assert payload[0]["status"] == "INPROGRESS"


class TestRedemptionAccuracy:

    def _confirmed_booking_fixture(self, client, session, email):
        headers = _auth_headers(client, email)
        user = session.query(User).filter_by(email=email).one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 101, RoomType.DOUBLE)
        booking = _make_booking(
            session, user, room,
            date(2027, 6, 1), date(2027, 6, 4),
            price="300.00",
        )
        booking.status = Status.CONFIRMED
        user.points = 500
        session.flush()
        return headers, booking, user

    def test_redeem_deducts_correct_points(self, reservation_client, session):
        headers, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test1.com"
        )
        before = user.points
        reservation_client.post(
            "/rewards/redeem",
            json={"points": 100, "booking_id": booking.id},
            headers=headers,
        )
        session.expire_all()
        assert session.get(User, user.id).points == before - 100

    def test_redeem_cannot_exceed_booking_total(self, reservation_client, session):
        headers, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test2.com"
        )
        user.points = 99999
        session.flush()
        excess_points = int(float(booking.total_price) * 100) + 500
        response = reservation_client.post(
            "/rewards/redeem",
            json={"points": excess_points, "booking_id": booking.id},
            headers=headers,
        )
        assert response.status_code == 400

    def test_points_not_deducted_on_failed_redemption(self, reservation_client, session):
        headers, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test3.com"
        )
        before = user.points
        reservation_client.post(
            "/rewards/redeem",
            json={"points": -50, "booking_id": booking.id},
            headers=headers,
        )
        session.expire_all()
        assert session.get(User, user.id).points == before

    def test_partial_redeem_leaves_correct_remainder(self, reservation_client, session):
        headers, booking, user = self._confirmed_booking_fixture(
            reservation_client, session, "test@test4.com"
        )
        points_to_use = 200
        balance_before = user.points
        total_before = booking.total_price
        reservation_client.post(
            "/rewards/redeem",
            json={"points": points_to_use, "booking_id": booking.id},
            headers=headers,
        )
        session.expire_all()
        updated_user = session.get(User, user.id)
        updated_booking = session.get(Booking, booking.id)
        assert updated_user.points == balance_before - points_to_use
        assert updated_booking.total_price == total_before - Decimal("2.00")

class TestCancelReservationPolicy:

    def test_cancellation_preview_requires_authentication(self, reservation_client, session):
        user = _make_user(session, "preview-noauth@example.com")
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 300, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=5),
            date.today() + timedelta(days=7),
        )

        response = reservation_client.get(f"/reservations/{booking.id}/cancellation-preview")

        assert response.status_code == 401

    def test_cancellation_requires_authentication(self, reservation_client, session):
        user = _make_user(session, "cancel-noauth@example.com")
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 304, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=6),
            date.today() + timedelta(days=8),
        )

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
        )

        assert response.status_code == 401

    def test_user_cannot_preview_another_users_booking(self, reservation_client, session):
        owner_headers = _auth_headers(reservation_client, "owner-preview@example.com")
        _ = owner_headers
        owner = session.query(User).filter_by(email="owner-preview@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 305, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            owner,
            room,
            date.today() + timedelta(days=5),
            date.today() + timedelta(days=7),
        )
        other_headers = _auth_headers(reservation_client, "other-preview@example.com")

        response = reservation_client.get(
            f"/reservations/{booking.id}/cancellation-preview",
            headers=other_headers,
        )

        assert response.status_code == 404
        assert response.get_json()["error"] == "Booking not found"

    def test_user_cannot_cancel_another_users_booking(self, reservation_client, session):
        owner_headers = _auth_headers(reservation_client, "owner-cancel@example.com")
        _ = owner_headers
        owner = session.query(User).filter_by(email="owner-cancel@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 306, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            owner,
            room,
            date.today() + timedelta(days=6),
            date.today() + timedelta(days=8),
        )
        other_headers = _auth_headers(reservation_client, "other-cancel@example.com")

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=other_headers,
        )

        assert response.status_code == 404
        assert response.get_json()["error"] == "Booking not found"

        session.expire_all()
        unchanged = session.get(Booking, booking.id)
        assert unchanged.status == Status.CONFIRMED

    def test_cancellation_preview_shows_refund_and_keeps_booking_active(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "cancel-preview@example.com")
        user = session.query(User).filter_by(email="cancel-preview@example.com").one()
        user.points = 550
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 301, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=5),
            date.today() + timedelta(days=7),
            price="185.00",
        )
        session.add_all([
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=200,
                log="Earned points for confirmation",
            ),
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=-150,
                log="Redeemed points at checkout",
            ),
        ])
        session.flush()

        response = reservation_client.get(
            f"/reservations/{booking.id}/cancellation-preview",
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["cancellation"]["fee_amount"] == "0.00"
        assert payload["cancellation"]["refund_amount"] == "185.00"
        assert payload["cancellation"]["points_to_restore"] == 150

        session.expire_all()
        unchanged = session.get(Booking, booking.id)
        assert unchanged.status == Status.CONFIRMED

    def test_cancellation_request_without_confirmation_returns_refund_details_and_keeps_status(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "cancel-quote@example.com")
        user = session.query(User).filter_by(email="cancel-quote@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 307, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=5),
            date.today() + timedelta(days=7),
            price="210.00",
        )

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["requires_confirmation"] is True
        assert payload["cancellation"]["refund_amount"] == "210.00"
        assert payload["cancellation"]["fee_amount"] == "0.00"

        session.expire_all()
        unchanged = session.get(Booking, booking.id)
        assert unchanged.status == Status.CONFIRMED

    def test_cancellation_within_48_hours_is_rejected_and_status_stays_same(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "cancel-blocked@example.com")
        user = session.query(User).filter_by(email="cancel-blocked@example.com").one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 302, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=3),
        )

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=headers,
        )

        assert response.status_code == 400
        payload = response.get_json()
        assert "48 hours" in payload["error"]

        session.expire_all()
        unchanged = session.get(Booking, booking.id)
        assert unchanged.status == Status.CONFIRMED

    def test_confirmed_cancellation_processes_refund_restores_points_and_updates_status(self, reservation_client, session):
        headers = _auth_headers(reservation_client, "cancel-success@example.com")
        user = session.query(User).filter_by(email="cancel-success@example.com").one()
        user.points = 550
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 303, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=6),
            date.today() + timedelta(days=8),
            price="185.00",
        )
        session.add_all([
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=200,
                log="Earned points for confirmation",
            ),
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=-150,
                log="Redeemed points at checkout",
            ),
        ])
        session.flush()

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["refund"]["processed"] is True
        assert payload["refund"]["amount"] == "185.00"
        assert payload["refund"]["fee_amount"] == "0.00"
        assert payload["refund"]["points_restored"] == 150

        session.expire_all()
        cancelled = session.get(Booking, booking.id)
        updated_user = session.get(User, user.id)
        assert cancelled.status == Status.CANCELLED
        assert updated_user.points == 500
    def test_cancellation_preview_uses_policy_fee_and_hours(
        self, reservation_client, session
        ):
        headers = _auth_headers(reservation_client, "cancel-policy-preview@example.com")
        user = session.query(User).filter_by(
            email="cancel-policy-preview@example.com"
        ).one()
        hotel = _make_hotel(session)
        _make_cancellation_policy(
            session, hotel, deadline_hours=72, fee_percent="15.00"
        )
        room = _make_typed_room(session, hotel, 401, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=7),
            date.today() + timedelta(days=9),
            price="200.00",
        )

        response = reservation_client.get(
            f"/reservations/{booking.id}/cancellation-preview",
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()["cancellation"]
        assert payload["policy_hours"] == 72
        assert payload["fee_percent"] == "15.00"
        assert payload["fee_amount"] == "30.00"
        assert payload["refund_amount"] == "170.00"

    def test_confirmed_cancellation_applies_policy_fee(
        self, reservation_client, session
        ):
        headers = _auth_headers(reservation_client, "cancel-policy-final@example.com")
        user = session.query(User).filter_by(
            email="cancel-policy-final@example.com"
        ).one()
        hotel = _make_hotel(session)
        _make_cancellation_policy(
            session, hotel, deadline_hours=72, fee_percent="20.00"
        )
        room = _make_typed_room(session, hotel, 402, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=8),
            date.today() + timedelta(days=10),
            price="250.00",
        )

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["refund"]["fee_amount"] == "50.00"
        assert payload["refund"]["amount"] == "200.00"

    def test_confirmed_cancellation_writes_points_logs(
        self, reservation_client, session
        ):
        headers = _auth_headers(reservation_client, "cancel-logs@example.com")
        user = session.query(User).filter_by(email="cancel-logs@example.com").one()
        user.points = 600
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 403, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=9),
            date.today() + timedelta(days=11),
            price="185.00",
        )
        session.add_all([
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=200,
                log="Earned points for confirmation",
            ),
            PointsTransaction(
                user_id=user.id,
                booking_id=booking.id,
                points=-150,
                log="Redeemed points at checkout",
            ),
        ])
        session.flush()

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=headers,
        )

        assert response.status_code == 200

        session.expire_all()
        logs = session.query(PointsTransaction).filter_by(booking_id=booking.id).all()
        log_messages = [entry.log for entry in logs]
        assert any("Reversed 200 earned points" in message for message in log_messages)
        assert any("Restored 150 redeemed points" in message for message in log_messages)

    def test_confirmed_cancellation_returns_email_sent_flag(
        self, reservation_client, session
        ):
        headers = _auth_headers(reservation_client, "cancel-email-flag@example.com")
        user = session.query(User).filter_by(
            email="cancel-email-flag@example.com"
        ).one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 404, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() + timedelta(days=10),
            date.today() + timedelta(days=12),
            price="185.00",
        )

        response = reservation_client.delete(
            f"/reservations/{booking.id}",
            json={"confirmed": True},
            headers=headers,
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert "email_sent" in payload
        assert payload["email_sent"] is False


# ── Rebook endpoint ──────────────────────────────────────────────────────────


class TestRebookBooking:

    def _setup_previous_booking(
        self, client, session, email, *, days_ago_start=30, days_ago_end=27
    ):
        headers = _auth_headers(client, email)
        user = session.query(User).filter_by(email=email).one()
        hotel = _make_hotel(session)
        room = _make_typed_room(session, hotel, 201, RoomType.DOUBLE)
        booking = _make_booking(
            session,
            user,
            room,
            date.today() - timedelta(days=days_ago_start),
            date.today() - timedelta(days=days_ago_end),
            price="300.00",
        )
        booking.status = Status.COMPLETED
        session.flush()
        return headers, user, hotel, room, booking

    def _seed_cache(self, hotel_id, rooms):
        from backend.search.routes import CachedHotel, _hotel_details_cache
        cached = CachedHotel()
        cached.rooms = rooms
        _hotel_details_cache[hotel_id] = cached
        return cached

    def _clear_cache(self, hotel_id):
        from backend.search.routes import _hotel_details_cache
        _hotel_details_cache.pop(hotel_id, None)

    def test_rebook_returns_previous_booking_details(
        self, reservation_client, session
    ):
        headers, _, hotel, room, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-details@example.com"
        )

        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook", headers=headers
        )

        assert response.status_code == 200
        payload = response.get_json()
        previous = payload["previous_booking"]
        assert previous["booking_id"] == booking.id
        assert previous["booking_number"] == booking.booking_number
        assert previous["title"] == booking.title
        assert previous["hotel_id"] == hotel.id
        assert previous["hotel_name"] == hotel.name
        assert previous["hotel_city"] == hotel.city
        assert previous["room"] == room.room
        assert previous["room_type"] == room.room_type.value
        assert previous["nights"] == 3
        assert previous["status"] == "COMPLETED"
        assert payload["rebook"]["hotel_id"] == hotel.id

    def test_rebook_defaults_to_original_trip_length(
        self, reservation_client, session
    ):
        headers, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-default-dates@example.com"
        )

        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook", headers=headers
        )

        assert response.status_code == 200
        rebook = response.get_json()["rebook"]
        assert rebook["start_date"] == date.today().isoformat()
        assert rebook["end_date"] == (
            date.today() + timedelta(days=3)
        ).isoformat()
        assert rebook["nights"] == 3

    def test_rebook_reports_room_available_for_open_dates(
        self, reservation_client, session
    ):
        headers, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-available@example.com"
        )

        new_start = (date.today() + timedelta(days=60)).isoformat()
        new_end = (date.today() + timedelta(days=63)).isoformat()
        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook"
            f"?start_date={new_start}&end_date={new_end}",
            headers=headers,
        )

        assert response.status_code == 200
        rebook = response.get_json()["rebook"]
        assert rebook["original_room_available"] is True
        assert rebook["conflicts"] == []
        assert rebook["alternative_rooms"] == []
        assert Decimal(rebook["estimated_total_price"]) == Decimal("300.00")

    def test_rebook_reports_conflict_with_cached_alternatives(
        self, reservation_client, session
    ):
        headers, user, hotel, room, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-conflict@example.com"
        )
        new_start = date.today() + timedelta(days=90)
        new_end = new_start + timedelta(days=3)
        # Block the original room for the new dates
        _make_booking(
            session, user, room, new_start, new_end, price="300.00"
        )
        # Seed the hotel cache with two extra rooms (302 + 303) and the
        # original (201). Only the unbooked extras should be returned.
        self._seed_cache(hotel.id, [
            {"room": 201, "room_type": "DOUBLE"},
            {"room": 302, "room_type": "TRIPLE"},
            {"room": 303, "room_type": "QUAD"},
        ])
        try:
            response = reservation_client.get(
                f"/reservations/{booking.id}/rebook"
                f"?start_date={new_start.isoformat()}"
                f"&end_date={new_end.isoformat()}",
                headers=headers,
            )
        finally:
            self._clear_cache(hotel.id)

        assert response.status_code == 200
        rebook = response.get_json()["rebook"]
        assert rebook["original_room_available"] is False
        assert len(rebook["conflicts"]) == 1
        alt_numbers = {r["room"] for r in rebook["alternative_rooms"]}
        assert alt_numbers == {302, 303}

    def test_rebook_returns_empty_alternatives_when_cache_missing(
        self, reservation_client, session
    ):
        headers, user, hotel, room, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-no-cache@example.com"
        )
        new_start = date.today() + timedelta(days=90)
        new_end = new_start + timedelta(days=3)
        _make_booking(
            session, user, room, new_start, new_end, price="300.00"
        )
        self._clear_cache(hotel.id)

        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook"
            f"?start_date={new_start.isoformat()}"
            f"&end_date={new_end.isoformat()}",
            headers=headers,
        )

        assert response.status_code == 200
        rebook = response.get_json()["rebook"]
        assert rebook["original_room_available"] is False
        assert rebook["alternative_rooms"] == []

    def test_rebook_rejects_past_start_date(
        self, reservation_client, session
    ):
        headers, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-past@example.com"
        )

        past_start = (date.today() - timedelta(days=1)).isoformat()
        past_end = (date.today() + timedelta(days=2)).isoformat()
        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook"
            f"?start_date={past_start}&end_date={past_end}",
            headers=headers,
        )

        assert response.status_code == 400
        payload = response.get_json()
        assert "start_date cannot be in the past" in payload["error"]
        assert payload["previous_booking"]["booking_id"] == booking.id

    def test_rebook_rejects_invalid_date_range(
        self, reservation_client, session
    ):
        headers, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-bad-range@example.com"
        )

        start = (date.today() + timedelta(days=10)).isoformat()
        end = (date.today() + timedelta(days=10)).isoformat()
        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook"
            f"?start_date={start}&end_date={end}",
            headers=headers,
        )

        assert response.status_code == 400
        assert "end_date must be after start_date" in response.get_json()["error"]

    def test_rebook_requires_both_dates_when_one_supplied(
        self, reservation_client, session
    ):
        headers, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-partial@example.com"
        )

        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook"
            f"?start_date={date.today().isoformat()}",
            headers=headers,
        )

        assert response.status_code == 400
        assert "must be provided together" in response.get_json()["error"]

    def test_rebook_returns_404_for_other_users_booking(
        self, reservation_client, session
    ):
        _, _, _, _, booking = self._setup_previous_booking(
            reservation_client, session, "rebook-owner@example.com"
        )
        other_headers = _auth_headers(reservation_client, "rebook-other@example.com")

        response = reservation_client.get(
            f"/reservations/{booking.id}/rebook", headers=other_headers
        )

        assert response.status_code == 404
        assert response.get_json()["error"] == "Booking not found"

    def test_rebook_requires_authentication(self, reservation_client):
        response = reservation_client.get("/reservations/1/rebook")
        assert response.status_code == 401


# ── Rebook flow integration (R07.4) ──────────────────────────────────────────


class TestRebookFlowIntegration:
    """
    End-to-end coverage of the rebook flow at the API level:
      1) GET /reservations/<id>/rebook to fetch previous booking + availability
      2) POST /reservations/ with the returned hotel_id + room number
    Includes the unavailable-original-room fallback described in R07.2/R07.4.
    """

    def _setup_user_and_hotel(self, client, session, email):
        headers = _auth_headers(client, email)
        user = session.query(User).filter_by(email=email).one()
        hotel = _make_hotel(session)
        return headers, user, hotel

    def _seed_cache(self, hotel_id, rooms):
        from backend.search.routes import CachedHotel, _hotel_details_cache
        cached = CachedHotel()
        cached.rooms = rooms
        _hotel_details_cache[hotel_id] = cached

    def _clear_cache(self, hotel_id):
        from backend.search.routes import _hotel_details_cache
        _hotel_details_cache.pop(hotel_id, None)

    def _completed_past_booking(self, session, user, room, *, days_ago=30):
        booking = _make_booking(
            session,
            user,
            room,
            date.today() - timedelta(days=days_ago),
            date.today() - timedelta(days=days_ago - 3),
            price="300.00",
        )
        booking.status = Status.COMPLETED
        session.flush()
        return booking

    def test_full_rebook_flow_when_original_room_available(
        self, reservation_client, session
    ):
        """Happy path: original room free → rebook info → POST a new booking on it."""
        headers, user, hotel = self._setup_user_and_hotel(
            reservation_client, session, "rebook-flow-happy@example.com"
        )
        original_room = _make_typed_room(session, hotel, 201, RoomType.DOUBLE)
        completed = self._completed_past_booking(session, user, original_room)

        new_start = (date.today() + timedelta(days=60)).isoformat()
        new_end = (date.today() + timedelta(days=63)).isoformat()

        # Step 1: ask the rebook endpoint for previous-booking + availability
        rebook_resp = reservation_client.get(
            f"/reservations/{completed.id}/rebook"
            f"?start_date={new_start}&end_date={new_end}",
            headers=headers,
        )
        assert rebook_resp.status_code == 200
        rebook_data = rebook_resp.get_json()
        assert rebook_data["rebook"]["original_room_available"] is True
        previous = rebook_data["previous_booking"]

        # Step 2: feed those values back into POST /reservations/
        create_resp = reservation_client.post(
            "/reservations/",
            json={
                "title": previous["title"],
                "hotel_id": previous["hotel_id"],
                "room": previous["room"],
                "start_date": new_start,
                "end_date": new_end,
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.get_json()["booking"]
        assert created["start_date"] == new_start
        assert created["end_date"] == new_end
        assert created["status"] == "INPROGRESS"

        # The new booking should be against the same physical room as the previous one
        session.expire_all()
        new_booking = session.get(Booking, created["id"])
        assert new_booking.room == original_room.id
        assert new_booking.id != completed.id

    def test_rebook_fallback_when_original_room_taken(
        self, reservation_client, session
    ):
        """Fallback: original room blocked → rebook returns alternatives → book one."""
        headers, user, hotel = self._setup_user_and_hotel(
            reservation_client, session, "rebook-flow-fallback@example.com"
        )
        original_room = _make_typed_room(session, hotel, 201, RoomType.DOUBLE)
        alt_room = _make_typed_room(session, hotel, 202, RoomType.TRIPLE)
        completed = self._completed_past_booking(session, user, original_room)

        new_start = date.today() + timedelta(days=90)
        new_end = new_start + timedelta(days=3)

        # Block the original room with a separate booking on the new dates
        blocker = User(email="blocker@example.com", password="hashed")
        session.add(blocker)
        session.flush()
        _make_booking(
            session, blocker, original_room, new_start, new_end, price="300.00"
        )

        # Seed the cache so alternatives are returned by /rebook
        self._seed_cache(hotel.id, [
            {"room": 201, "room_type": "DOUBLE"},
            {"room": 202, "room_type": "TRIPLE"},
        ])

        try:
            rebook_resp = reservation_client.get(
                f"/reservations/{completed.id}/rebook"
                f"?start_date={new_start.isoformat()}"
                f"&end_date={new_end.isoformat()}",
                headers=headers,
            )
            assert rebook_resp.status_code == 200
            rebook_data = rebook_resp.get_json()
            assert rebook_data["rebook"]["original_room_available"] is False
            alt_numbers = [r["room"] for r in rebook_data["rebook"]["alternative_rooms"]]
            assert alt_room.room in alt_numbers

            # Booking the original room should now fail with a conflict
            blocked_resp = reservation_client.post(
                "/reservations/",
                json={
                    "title": "Retry on original",
                    "hotel_id": hotel.id,
                    "room": original_room.room,
                    "start_date": new_start.isoformat(),
                    "end_date": new_end.isoformat(),
                },
                headers=headers,
            )
            assert blocked_resp.status_code == 409

            # Booking the suggested alternative room should succeed
            alt_resp = reservation_client.post(
                "/reservations/",
                json={
                    "title": "Alternative room rebook",
                    "hotel_id": hotel.id,
                    "room": alt_room.room,
                    "start_date": new_start.isoformat(),
                    "end_date": new_end.isoformat(),
                },
                headers=headers,
            )
            assert alt_resp.status_code == 201
            created = alt_resp.get_json()["booking"]
            session.expire_all()
            new_booking = session.get(Booking, created["id"])
            assert new_booking.room == alt_room.id
        finally:
            self._clear_cache(hotel.id)

    def test_rebook_then_create_uses_today_default_dates(
        self, reservation_client, session
    ):
        """Without query params, /rebook returns today + original trip length, and POST works on those defaults."""
        headers, user, hotel = self._setup_user_and_hotel(
            reservation_client, session, "rebook-flow-defaults@example.com"
        )
        original_room = _make_typed_room(session, hotel, 301, RoomType.SINGLE)
        completed = self._completed_past_booking(session, user, original_room)

        rebook_resp = reservation_client.get(
            f"/reservations/{completed.id}/rebook", headers=headers
        )
        assert rebook_resp.status_code == 200
        data = rebook_resp.get_json()
        suggested_start = data["rebook"]["start_date"]
        suggested_end = data["rebook"]["end_date"]
        assert suggested_start == date.today().isoformat()
        assert suggested_end == (date.today() + timedelta(days=3)).isoformat()

        create_resp = reservation_client.post(
            "/reservations/",
            json={
                "title": data["previous_booking"]["title"],
                "hotel_id": data["previous_booking"]["hotel_id"],
                "room": data["previous_booking"]["room"],
                "start_date": suggested_start,
                "end_date": suggested_end,
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
