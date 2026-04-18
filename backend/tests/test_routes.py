from datetime import date, timedelta
from decimal import Decimal
from backend.db.models import Hotel

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


class TestPasswordReset:

    def test_forgot_password_returns_token_for_existing_email(self, client):
        client.post('/auth/register', json={
            'name': 'Reset User',
            'email': 'reset@example.com',
            'password': 'oldpass',
        })

        response = client.post('/auth/forgot-password', json={
            'email': 'reset@example.com',
        })

        assert response.status_code == 200
        payload = response.get_json()
        assert "password reset steps" in payload["message"]
        assert isinstance(payload["reset_token"], str)

    def test_forgot_password_rejects_unknown_email(self, client):
        response = client.post('/auth/forgot-password', json={
            'email': 'unknown@example.com',
        })

        assert response.status_code == 404
        assert response.get_json() == {
            "error": "There is no account associated with the email"
        }

    def test_forgot_password_rejects_invalid_email_format(self, client):
        response = client.post('/auth/forgot-password', json={
            'email': 'not-an-email',
        })

        assert response.status_code == 400
        assert response.get_json() == {
            "error": "The email is invalid"
        }

    def test_forgot_password_rejects_invalid_domain_edge_cases(self, client):
        invalid_emails = [
            'wafhanowjmoqwp@.gnail.com',
            'wafhanowjmoqwp@gmail..com',
            'wafhanowjmoqwp@gmail.',
            'wafhanowjmoqwp@gmail.c',
        ]

        for email in invalid_emails:
            response = client.post('/auth/forgot-password', json={'email': email})
            assert response.status_code == 400
            assert response.get_json() == {"error": "The email is invalid"}

    def test_reset_password_updates_login_password(self, client):
        client.post('/auth/register', json={
            'name': 'Reset Login User',
            'email': 'reset-login@example.com',
            'password': 'oldpass',
        })
        token = client.post('/auth/forgot-password', json={
            'email': 'reset-login@example.com',
        }).get_json()["reset_token"]

        response = client.post('/auth/reset-password', json={
            'token': token,
            'password': 'newpass123',
        })

        assert response.status_code == 200
        assert response.get_json() == {"message": "Password updated"}

        old_login = client.post('/auth/login', json={
            'email': 'reset-login@example.com',
            'password': 'oldpass',
        })
        assert old_login.status_code == 401

        new_login = client.post('/auth/login', json={
            'email': 'reset-login@example.com',
            'password': 'newpass123',
        })
        assert new_login.status_code == 200
        assert "access_token" in new_login.get_json()

    def test_reset_password_rejects_bad_token(self, client):
        response = client.post('/auth/reset-password', json={
            'token': 'not-a-real-token',
            'password': 'newpass123',
        })

        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid reset token"}


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
