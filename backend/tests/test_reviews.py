import pytest
from unittest.mock import patch
from backend.db.models import Hotel, Review, Booking, HotelRoom, Status, User


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_hotel(session):
    h = Hotel(
        name="Test Hotel",
        price_per_night=100.00,
        city="San Jose",
        address="1 Main St",
    )
    session.add(h)
    session.flush()
    return h


def _make_room(session, hotel):
    from backend.db.models import RoomType
    r = HotelRoom(hotel=hotel.id, room=101, room_type=RoomType.DOUBLE)
    session.add(r)
    session.flush()
    return r


def _make_booking(session, user, room, status=Status.COMPLETED):
    from datetime import date
    from backend.reservation.utils import generate_booking_number
    b = Booking(
        booking_number=generate_booking_number(),
        title="Test Stay",
        user=user.id,
        room=room.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 3),
        total_price=200.00,
        status=status,
    )
    session.add(b)
    session.flush()
    return b


def _make_review(session, user, hotel, rating=5):
    r = Review(
        user=user.id,
        hotel=hotel.id,
        title="Great stay",
        content="Loved every minute",
        rating=rating,
    )
    session.add(r)
    session.flush()
    return r



@pytest.fixture()
def review_client(client, session):
    yield client


def _auth_headers(client, email="reviewer@example.com"):
    client.post("/auth/register", json={
        "name": "Reviewer",
        "email": email,
        "password": "password123",
    })
    res = client.post("/auth/login", json={"email": email, "password": "password123"})
    token = res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── POST /hotels/<id>/reviews ─────────────────────────────────────────────────


class TestCreateReview:

    def test_create_review_success(self, review_client, session):
        headers = _auth_headers(review_client, "post-success@example.com")
        user = session.query(User).filter_by(email="post-success@example.com").one()
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room, status=Status.COMPLETED)
        session.flush()

        res = review_client.post(f"/hotels/{hotel.id}/reviews", json={
            "rating": 5,
            "title": "Great stay",
            "content": "Loved every minute",
        }, headers=headers)

        assert res.status_code == 201
        assert res.get_json()["message"] == "Review created"

    def test_create_review_no_stay(self, review_client, session):
        headers = _auth_headers(review_client, "post-nostay@example.com")
        hotel = _make_hotel(session)

        res = review_client.post(f"/hotels/{hotel.id}/reviews", json={
            "rating": 3,
            "title": "Ok",
            "content": "It was fine",
        }, headers=headers)

        assert res.status_code == 403
        assert "stayed" in res.get_json()["error"]


# ── PATCH /hotels/<id>/reviews/<review_id> ────────────────────────────────────


class TestEditReview:

    def test_edit_review_success(self, review_client, session):
        headers = _auth_headers(review_client, "edit-success@example.com")
        user = session.query(User).filter_by(email="edit-success@example.com").one()
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room)
        review = _make_review(session, user, hotel)

        res = review_client.patch(f"/hotels/{hotel.id}/reviews/{review.id}", json={
            "rating": 3,
            "title": "Changed mind",
            "content": "It was just okay",
        }, headers=headers)

        assert res.status_code == 200
        assert res.get_json()["message"] == "Review updated"

        session.expire_all()
        updated = session.get(Review, review.id)
        assert updated.rating == 3
        assert updated.title == "Changed mind"


# ── DELETE /hotels/<id>/reviews/<review_id> ───────────────────────────────────


class TestDeleteReview:

    def test_delete_review_success(self, review_client, session):
        headers = _auth_headers(review_client, "delete-success@example.com")
        user = session.query(User).filter_by(email="delete-success@example.com").one()
        hotel = _make_hotel(session)
        room = _make_room(session, hotel)
        _make_booking(session, user, room)
        review = _make_review(session, user, hotel)

        res = review_client.delete(f"/hotels/{hotel.id}/reviews/{review.id}", headers=headers)

        assert res.status_code == 200
        assert res.get_json()["message"] == "Review deleted"

        session.expire_all()
        assert session.get(Review, review.id) is None