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
