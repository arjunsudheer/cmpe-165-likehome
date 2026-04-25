import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from backend.db.models import Hotel
from backend.auth.password_utils import hash_password
from backend.db.models import PasswordResetToken, User

class TestRegistration:

    def test_accept_valid_registration(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'test@email.com',
            'password': 'password',
            'confirm_password': 'password'
        })
        assert response.status_code == 201
        json_resp = response.get_json()
        assert "access_token" in json_resp
        assert json_resp["email"] == "test@email.com"
        assert json_resp["name"] == "Test User"

    def test_accept_missing_name(self, client):
        response = client.post('/auth/register', json={
            'email': 'noname@example.com',
            'password': 'password',
        })
        assert response.status_code == 201

    def test_reject_empty_email_field(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': '',
            'password': 'password',
        })
        assert response.status_code == 400

    def test_reject_empty_password_field(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'test2@email.com',
            'password': '',
        })
        assert response.status_code == 400

    def test_reject_invalid_email_format(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'email.com',
            'password': 'password',
        })
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid email format"}

    def test_reject_under_minimum_password_length(self, client):
        response = client.post('/auth/register', json={
            'name': 'Test User',
            'email': 'short@email.com',
            'password': 'pass',
        })
        assert response.status_code == 400
        assert response.get_json() == {"error": "Password must be at least 6 characters"}

    def test_reject_duplicate_email(self, client):
        client.post('/auth/register', json={
            'name': 'User One',
            'email': 'duplicate@email.com',
            'password': 'password',
        })
        response = client.post('/auth/register', json={
            'name': 'User Two',
            'email': 'duplicate@email.com',
            'password': 'password',
        })
        assert response.status_code == 409
        assert response.get_json() == {"error": "email_exists"}

    def test_reject_different_case_duplicate_email(self, client):
        client.post('/auth/register', json={
            'name': 'User One',
            'email': 'dupcase@email.com',
            'password': 'password',
        })
        response = client.post('/auth/register', json={
            'name': 'User Two',
            'email': 'Dupcase@email.com',
            'password': 'password',
        })
        assert response.status_code == 409
        assert response.get_json() == {"error": "email_exists"}


class TestHotelSorting:

    def _seed_hotels(self, session):
        hotels = [
            Hotel(
                name="Budget Inn",
                price_per_night=Decimal("80.00"),
                rating=Decimal("3.20"),
                city="San Jose",
                address="101 First St",
            ),
            Hotel(
                name="Comfort Stay",
                price_per_night=Decimal("120.00"),
                rating=Decimal("4.50"),
                city="San Francisco",
                address="202 Second St",
            ),
            Hotel(
                name="Luxury Suites",
                price_per_night=Decimal("200.00"),
                rating=Decimal("4.80"),
                city="San Diego",
                address="303 Third St",
            ),
        ]
        session.add_all(hotels)
        session.commit()

    def test_get_all_hotels_sorted_by_price_asc(self, client, session):
        self._seed_hotels(session)

        response = client.get("/hotels/?sort=price&order=asc")
        assert response.status_code == 200

        data = response.get_json()
        prices = [hotel["price_per_night"] for hotel in data["results"]]
        assert prices == sorted(prices)

    def test_get_all_hotels_sorted_by_price_desc(self, client, session):
        self._seed_hotels(session)

        response = client.get("/hotels/?sort=price&order=desc")
        assert response.status_code == 200

        data = response.get_json()
        prices = [hotel["price_per_night"] for hotel in data["results"]]
        assert prices == sorted(prices, reverse=True)

    def test_get_all_hotels_sorted_by_rating_desc(self, client, session):
        self._seed_hotels(session)

        response = client.get("/hotels/?sort=rating&order=desc")
        assert response.status_code == 200

        data = response.get_json()
        ratings = [hotel["rating"] for hotel in data["results"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_get_all_hotels_sorted_by_rating_asc(self, client, session):
        self._seed_hotels(session)

        response = client.get("/hotels/?sort=rating&order=asc")
        assert response.status_code == 200

        data = response.get_json()
        ratings = [hotel["rating"] for hotel in data["results"]]
        assert ratings == sorted(ratings)

    def test_search_hotels_sorted_by_price_asc(self, client, session):
        self._seed_hotels(session)

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        day_after = (date.today() + timedelta(days=2)).isoformat()

        response = client.get(
            f"/hotels/search?destination=San&check_in={tomorrow}&check_out={day_after}&sort=price&order=asc"
        )
        assert response.status_code == 200

        data = response.get_json()
        prices = [hotel["price_per_night"] for hotel in data["results"]]
        assert prices == sorted(prices)

    def test_invalid_sort_defaults_safely(self, client, session):
        self._seed_hotels(session)

        response = client.get("/hotels/?sort=banana&order=sideways")
        assert response.status_code == 200

        data = response.get_json()
        ratings = [hotel["rating"] for hotel in data["results"]]
        assert ratings == sorted(ratings, reverse=True)


class TestPasswordReset:

    def test_forgot_password_returns_dev_token_for_existing_user(self, client, session):
        session.add(
            User(
                name="Reset User",
                email="reset@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        with patch("backend.auth.routes.send_email") as mock_send_email:
            response = client.post(
                "/auth/forgot-password",
                json={"email": "reset@example.com"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "reset_token" in data
        assert data["message"].startswith("If an account exists")
        mock_send_email.assert_called_once()

        reset_record = session.query(PasswordResetToken).one()
        assert reset_record.used_at is None
        assert reset_record.expires_at > datetime.now(UTC).replace(tzinfo=None)
        assert reset_record.token_hash != data["reset_token"]

    def test_forgot_password_is_generic_for_unknown_email(self, client, session):
        with patch("backend.auth.routes.send_email") as mock_send_email:
            response = client.post(
                "/auth/forgot-password",
                json={"email": "missing@example.com"},
            )

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "If an account exists for that email, we have sent password reset instructions."
        }
        mock_send_email.assert_not_called()
        assert session.query(PasswordResetToken).count() == 0

    def test_reset_password_updates_password_and_consumes_token(self, client, session):
        session.add(
            User(
                name="Reset User",
                email="reset2@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        forgot = client.post(
            "/auth/forgot-password",
            json={"email": "reset2@example.com"},
        )
        token = forgot.get_json()["reset_token"]

        response = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "newpassword"},
        )
        assert response.status_code == 200
        assert response.get_json() == {"message": "Password updated successfully"}

        login_old = client.post(
            "/auth/login",
            json={"email": "reset2@example.com", "password": "oldpassword"},
        )
        assert login_old.status_code == 401

        login_new = client.post(
            "/auth/login",
            json={"email": "reset2@example.com", "password": "newpassword"},
        )
        assert login_new.status_code == 200

        reset_record = session.query(PasswordResetToken).one()
        assert reset_record.used_at is not None

    def test_reset_password_rejects_expired_token(self, client, session):
        user = User(
            name="Expired User",
            email="expired@example.com",
            password=hash_password("oldpassword"),
        )
        session.add(user)
        session.commit()

        raw_token = "expired-token"
        session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
                expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
            )
        )
        session.commit()

        response = client.post(
            "/auth/reset-password",
            json={"token": raw_token, "password": "newpassword"},
        )

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "This reset link is invalid or has expired"
        }

    def test_reset_password_rejects_reusing_current_password(self, client, session):
        session.add(
            User(
                name="Repeat User",
                email="repeat@example.com",
                password=hash_password("samepassword"),
            )
        )
        session.commit()

        forgot = client.post(
            "/auth/forgot-password",
            json={"email": "repeat@example.com"},
        )
        token = forgot.get_json()["reset_token"]

        response = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "samepassword"},
        )

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "Choose a new password that is different from your current password"
        }

        login_same = client.post(
            "/auth/login",
            json={"email": "repeat@example.com", "password": "samepassword"},
        )
        assert login_same.status_code == 200

        reset_record = session.query(PasswordResetToken).one()
        assert reset_record.used_at is None

    def test_validate_reset_password_accepts_active_token(self, client, session):
        session.add(
            User(
                name="Validate User",
                email="validate@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        forgot = client.post(
            "/auth/forgot-password",
            json={"email": "validate@example.com"},
        )
        token = forgot.get_json()["reset_token"]

        response = client.get(
            f"/auth/reset-password/validate?token={token}"
        )

        assert response.status_code == 200
        assert response.get_json() == {"message": "Reset link is valid"}

    def test_validate_reset_password_rejects_used_token(self, client, session):
        session.add(
            User(
                name="Used User",
                email="used@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        forgot = client.post(
            "/auth/forgot-password",
            json={"email": "used@example.com"},
        )
        token = forgot.get_json()["reset_token"]

        reset = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "newpassword"},
        )
        assert reset.status_code == 200

        response = client.get(
            f"/auth/reset-password/validate?token={token}"
        )

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "This reset link is invalid or has expired"
        }
