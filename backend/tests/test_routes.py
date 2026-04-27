import hashlib
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
import pytest

from backend.db.models import Hotel
from backend.auth.password_utils import hash_password
from backend.db.models import PasswordResetToken, User, SavedSearch

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


class TestGoogleLogin:
    # These tests pin the backend contract used by the dedicated Google sign-in page.

    def test_reject_missing_credential(self, client):
        client.application.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"

        response = client.post("/auth/google", json={})

        assert response.status_code == 400
        assert response.get_json() == {"error": "credential is required"}

    def test_reject_when_google_oauth_is_not_configured(self, client):
        client.application.config["GOOGLE_CLIENT_ID"] = ""

        response = client.post("/auth/google", json={"credential": "fake-token"})

        assert response.status_code == 501
        assert response.get_json() == {
            "error": "Google OAuth is not configured on this server"
        }

    def test_reject_invalid_google_token(self, client):
        client.application.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"

        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            side_effect=ValueError("Token used too late"),
        ):
            response = client.post("/auth/google", json={"credential": "bad-token"})

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "Invalid Google token: Token used too late"
        }

    def test_google_login_creates_new_user(self, client, session):
        client.application.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"

        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={
                "email": "googleuser@example.com",
                "name": "Google User",
            },
        ):
            response = client.post("/auth/google", json={"credential": "valid-token"})

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert data["email"] == "googleuser@example.com"
        assert data["name"] == "Google User"

        user = session.query(User).filter_by(email="googleuser@example.com").one()
        assert user.name == "Google User"
        assert user.password

    def test_google_login_reuses_existing_user(self, client, session):
        client.application.config["GOOGLE_CLIENT_ID"] = "test-google-client-id"
        existing_user = User(
            name="Existing User",
            email="existing-google@example.com",
            password=hash_password("password123"),
        )
        session.add(existing_user)
        session.commit()

        with patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={
                "email": "existing-google@example.com",
                "name": "Google Name That Should Not Replace Existing",
            },
        ):
            response = client.post("/auth/google", json={"credential": "valid-token"})

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_id"] == existing_user.id
        assert data["email"] == "existing-google@example.com"
        assert session.query(User).filter_by(email="existing-google@example.com").count() == 1


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

    def test_forgot_password_rejects_invalid_email(self, client):
        response = client.post(
            "/auth/forgot-password",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid email format"}

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

    def test_forgot_password_invalidates_previous_unused_token(self, client, session):
        session.add(
            User(
                name="Reset User",
                email="rotate@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        first = client.post(
            "/auth/forgot-password",
            json={"email": "rotate@example.com"},
        )
        first_token = first.get_json()["reset_token"]

        second = client.post(
            "/auth/forgot-password",
            json={"email": "rotate@example.com"},
        )
        second_token = second.get_json()["reset_token"]

        assert first_token != second_token

        first_reset = client.post(
            "/auth/reset-password",
            json={"token": first_token, "password": "brandnewpassword"},
        )
        assert first_reset.status_code == 400
        assert first_reset.get_json() == {
            "error": "This reset link is invalid or has expired"
        }

        second_reset = client.post(
            "/auth/reset-password",
            json={"token": second_token, "password": "brandnewpassword"},
        )
        assert second_reset.status_code == 200

        reset_records = session.query(PasswordResetToken).order_by(PasswordResetToken.id).all()
        assert len(reset_records) == 2
        assert reset_records[0].used_at is not None
        assert reset_records[1].used_at is not None

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

    def test_reset_password_requires_token(self, client):
        response = client.post(
            "/auth/reset-password",
            json={"password": "newpassword"},
        )

        assert response.status_code == 400
        assert response.get_json() == {"error": "token is required"}

    def test_reset_password_rejects_short_password(self, client, session):
        session.add(
            User(
                name="Short User",
                email="short@example.com",
                password=hash_password("oldpassword"),
            )
        )
        session.commit()

        forgot = client.post(
            "/auth/forgot-password",
            json={"email": "short@example.com"},
        )
        token = forgot.get_json()["reset_token"]

        response = client.post(
            "/auth/reset-password",
            json={"token": token, "password": "123"},
        )

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "Password must be at least 6 characters"
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

    def test_validate_reset_password_requires_token(self, client):
        response = client.get("/auth/reset-password/validate")

        assert response.status_code == 400
        assert response.get_json() == {"error": "token is required"}

class TestSavedSearch:

    CHECK_IN = (date.today() + timedelta(days=1)).isoformat()
    CHECK_OUT = (date.today() + timedelta(days=8)).isoformat()

    @pytest.fixture()
    def auth_headers(self, client):
        client.post("/auth/register", json={
            "name": "Test User",
            "email": "user@email.com",
            "password": "password",
        })
        response = client.post("/auth/login", json={
            "email": "user@email.com",
            "password": "password",
        })
        return {"Authorization": f"Bearer {response.get_json()['access_token']}"}

    @pytest.fixture()
    def saved_search(self, client, auth_headers):
        resp = client.post("/saved-searches/", json={
            "destination": "San Jose",
            "check_in": self.CHECK_IN,
            "check_out": self.CHECK_OUT,
            "guests": 1,
            "max_price": 250,
            "min_rating": 4,
            "amenities": ["Spa"],
            "sort_field": "price",
            "sort_order": "asc",
        }, headers=auth_headers)
        return resp.get_json()

    def test_create_saved_search(self, client, auth_headers):
        resp = client.post("/saved-searches/", json={
            "destination": "San Jose",
            "check_in": self.CHECK_IN,
            "check_out": self.CHECK_OUT,
            "guests": 1,
            "max_price": 250,
            "amenities": ["Free Wifi"],
            "sort_field": "price",
            "sort_order": "asc",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert "id" in resp.get_json()
        assert resp.get_json()["id"] is not None

    def test_create_rejects_invalid_date(self, client, auth_headers):
        resp = client.post("/saved-searches/", json={
            "destination": "San Jose",
            "check_in": "??",
            "check_out": self.CHECK_OUT,
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_get_saved_searches(self, client, auth_headers, saved_search):
        resp = client.get("/saved-searches/", headers=auth_headers)
        assert resp.status_code == 200
        results = resp.get_json()["results"]
        assert len(results) == 1
        assert results[0]["destination"] == "San Jose"
        for field in ("id", "destination", "checkIn", "checkOut", "guests", "filters", "sorting", "savedAt"):
            assert field in results[0]

    def test_get_only_returns_own_searches(self, client):
        client.post("/auth/register", json={
            "name": "Another User",
            "email": "test@email.com",
            "password": "password",
        })
        resp = client.post("/auth/login", json={"email": "test@email.com", "password": "password"})
        other_headers = {"Authorization": f"Bearer {resp.get_json()['access_token']}"}
        data = client.get("/saved-searches/", headers=other_headers).get_json()
        assert data["results"] == []

    def test_delete_saved_search(self, client, session, auth_headers, saved_search):
        resp = client.delete(f"/saved-searches/{saved_search['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert session.get(SavedSearch, saved_search["id"]) is None

    def test_delete_requires_auth(self, client, saved_search):
        resp = client.delete(f"/saved-searches/{saved_search['id']}")
        assert resp.status_code == 401

    def test_apply_saved_search(self, client, session, saved_search):
        session.add(Hotel(name="Hotel", city="San Jose", address="1 Main St", price_per_night=100.00, rating=4.0))
        session.commit()
        data = client.get(f"/hotels/search?saved_search_id={saved_search['id']}").get_json()
        assert data["destination"] == "San Jose"
        assert data["check_in"] == self.CHECK_IN
        assert data["check_out"] == self.CHECK_OUT
        assert data["filters"]["max_price"] == 250
        assert len(data["results"]) > 0
