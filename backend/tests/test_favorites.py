from decimal import Decimal
from unittest.mock import patch

import pytest
from backend.db.models import Favorite, Hotel, User


def _make_user(session, email="user@example.com"):
    u = User(email=email, password="hashed")
    session.add(u)
    session.flush()
    return u


def _make_hotel(session, name="Hotel A", address="1 Test St"):
    h = Hotel(
        name=name,
        price_per_night=Decimal("120.00"),
        city="San Jose",
        address=address,
    )
    session.add(h)
    session.flush()
    return h


@pytest.fixture()
def fav_client(client, session):
    bind = session.get_bind()
    with patch("backend.favorites.routes.engine", bind):
        yield client


def _auth_headers(client, email="fav@example.com"):
    resp = client.post("/auth/register", json={
        "name": "Fav User",
        "email": email,
        "password": "password123",
    })
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


class TestAddFavorite:

    def test_add_hotel_to_favorites(self, fav_client, session):
        hotel = _make_hotel(session, address="10 Fav St")
        headers = _auth_headers(fav_client, "add@example.com")

        resp = fav_client.post(f"/favorites/{hotel.id}", headers=headers)

        assert resp.status_code == 201
        assert resp.get_json()["hotel_id"] == hotel.id

    def test_add_nonexistent_hotel_returns_404(self, fav_client, session):
        headers = _auth_headers(fav_client, "add2@example.com")

        resp = fav_client.post("/favorites/99999", headers=headers)

        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Hotel not found"}

    def test_add_duplicate_returns_409(self, fav_client, session):
        hotel = _make_hotel(session, address="11 Fav St")
        headers = _auth_headers(fav_client, "dup@example.com")

        fav_client.post(f"/favorites/{hotel.id}", headers=headers)
        resp = fav_client.post(f"/favorites/{hotel.id}", headers=headers)

        assert resp.status_code == 409
        assert resp.get_json() == {"error": "Already in favorites"}

    def test_add_requires_auth(self, fav_client, session):
        hotel = _make_hotel(session, address="12 Fav St")
        resp = fav_client.post(f"/favorites/{hotel.id}")
        assert resp.status_code == 401


class TestRemoveFavorite:

    def test_remove_existing_favorite(self, fav_client, session):
        hotel = _make_hotel(session, address="20 Fav St")
        headers = _auth_headers(fav_client, "rm@example.com")

        fav_client.post(f"/favorites/{hotel.id}", headers=headers)
        resp = fav_client.delete(f"/favorites/{hotel.id}", headers=headers)

        assert resp.status_code == 200
        assert resp.get_json()["hotel_id"] == hotel.id

    def test_remove_not_in_favorites_returns_404(self, fav_client, session):
        hotel = _make_hotel(session, address="21 Fav St")
        headers = _auth_headers(fav_client, "rm2@example.com")

        resp = fav_client.delete(f"/favorites/{hotel.id}", headers=headers)

        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Not in favorites"}

    def test_remove_requires_auth(self, fav_client, session):
        hotel = _make_hotel(session, address="22 Fav St")
        resp = fav_client.delete(f"/favorites/{hotel.id}")
        assert resp.status_code == 401


class TestListFavorites:

    def test_list_empty_favorites(self, fav_client, session):
        headers = _auth_headers(fav_client, "list0@example.com")

        resp = fav_client.get("/favorites/", headers=headers)

        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_shows_added_hotels(self, fav_client, session):
        hotel1 = _make_hotel(session, name="Hotel X", address="30 Fav St")
        hotel2 = _make_hotel(session, name="Hotel Y", address="31 Fav St")
        headers = _auth_headers(fav_client, "list1@example.com")

        fav_client.post(f"/favorites/{hotel1.id}", headers=headers)
        fav_client.post(f"/favorites/{hotel2.id}", headers=headers)
        resp = fav_client.get("/favorites/", headers=headers)

        assert resp.status_code == 200
        ids = [h["hotel_id"] for h in resp.get_json()]
        assert hotel1.id in ids
        assert hotel2.id in ids

    def test_list_only_returns_own_favorites(self, fav_client, session):
        hotel = _make_hotel(session, address="40 Fav St")
        headers_a = _auth_headers(fav_client, "usera@example.com")
        headers_b = _auth_headers(fav_client, "userb@example.com")

        fav_client.post(f"/favorites/{hotel.id}", headers=headers_a)
        resp = fav_client.get("/favorites/", headers=headers_b)

        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_list_requires_auth(self, fav_client):
        resp = fav_client.get("/favorites/")
        assert resp.status_code == 401
