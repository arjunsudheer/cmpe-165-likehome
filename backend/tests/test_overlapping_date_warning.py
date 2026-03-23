from playwright.sync_api import Page, expect
import requests
import pytest

FRONTEND_URL = "http://127.0.0.1:5173"
API_URL = "http://127.0.0.1:5000"

class TestOverlapWarning:

    @pytest.fixture(autouse=True)
    def create_mock_booking(self):
        register = requests.post(f"{API_URL}/auth/register", json={
        'name': "User Name",
        'email': 'user@email.com',
        'password': 'password'
        })
        if 'access_token' in register.json():
            token = register.json()['access_token']
            self.user_id = register.json()['user_id']
        else:
            login = requests.post(f"{API_URL}/auth/login", json={
                'email': 'user@email.com',
                'password': 'password'
            })
            token = login.json()['access_token']
            self.user_id = login.json()['user_id']
        self.headers = {'Authorization': f'Bearer {token}'}

        response = requests.post(f"{API_URL}/reservations/", json={
            'title': 'Test Trip',
            'room': '10',
            'start_date': '2027-01-01',
            'end_date': '2027-01-10'
        }, headers=self.headers)
        print(response.json()) 
        self.booking_id = response.json()['booking']['id']
        yield 

    def test_warning_display(self, page: Page):
        page.goto(f"{FRONTEND_URL}/login")
        page.fill("input[type='email']", "user@email.com")
        page.fill("input[type='password']", "password")
        page.click("button[type='submit']")
        page.wait_for_url(f"{FRONTEND_URL}")

        page.goto(f"{FRONTEND_URL}/booking/1")
        page.fill("input[type='text']", "Trip")
        page.locator("input[type='date']").nth(0).fill("2027-01-02")
        page.locator("input[type='date']").nth(1).fill("2027-01-10")
        page.fill("input[type='number']", "4")
        page.click("button:has-text('Check Availability')")
        expect(page.locator('.conflict-bookings')).to_be_visible()