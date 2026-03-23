from backend.db.queries import get_overlapping_booking_dates
from sqlalchemy import delete
from backend.db.models import Booking, User, HotelRoom, Hotel, RoomType
from datetime import date
import pytest

# pylint: disable=attribute-defined-outside-init
class TestBooking:

    @pytest.fixture(autouse=True)
    def create_mock_booking(self, session):
        user = User(email='user@email.com', password='password')
        session.add(user)
        session.flush()
        hotel = Hotel(name="The Hotel", price_per_night=100.00, city="San Jose", address="123 Main St")
        session.add(hotel)
        session.flush()
        room = HotelRoom(hotel=hotel.id, room=1, room_type=RoomType.DOUBLE)
        session.add(room)
        session.flush()
        booking = Booking(booking_number=1, title='Trip', user=user.id, room=room.id, start_date=date(2027, 1, 1), end_date=date(2027, 1, 5), total_price=100.99)
        session.add(booking)
        session.flush()
        self.user_id = user.id 
        self.booking_id = booking.id

    def test_left_overlapping_booking_dates(self):
        left_overlap_result = get_overlapping_booking_dates(self.user_id, date(2027, 1, 2), date(2027, 1, 6)) 
        assert left_overlap_result[0][0] == self.booking_id

    def test_right_overlapping_booking_dates(self):
        right_overlap_result = get_overlapping_booking_dates(self.user_id, date(2026, 12, 31), date(2027, 1, 3)) 
        assert right_overlap_result[0][0] == self.booking_id

    def test_exact_overlapping_booking_dates(self):
        exact_overlap_result = get_overlapping_booking_dates(self.user_id, date(2026, 1, 1), date(2027, 1, 5)) 
        assert exact_overlap_result[0][0] == self.booking_id

    def test_inner_overlapping_booking_dates(self):
        inner_overlap_result = get_overlapping_booking_dates(self.user_id, date(2027, 1, 2), date(2027, 1, 4))
        assert inner_overlap_result[0][0] == self.booking_id

    def test_no_overlapping_booking_dates(self):
        no_overlap_result = get_overlapping_booking_dates(self.user_id, date(2028, 1, 2), date(2028, 1, 6))
        assert no_overlap_result == []

    def test_multiple_overlapping_booking_dates(self, session):
        hotel = Hotel(name="New Hotel", price_per_night=100.00, city="San Jose", address="1234 Main St")
        session.add(hotel)
        session.flush()
        room = HotelRoom(hotel=hotel.id, room=1, room_type=RoomType.DOUBLE)
        session.add(room)
        session.flush()
        booking = Booking(booking_number=2, title='Fun Trip', user=self.user_id, room=room.id, start_date=date(2027, 1, 6), end_date=date(2027, 1, 10), total_price=100.99)
        session.add(booking)
        session.flush()
        new_booking_id = booking.id
        multiple_overlap_result = get_overlapping_booking_dates(self.user_id, date(2027, 1, 1), date(2027, 1, 14))
        booking_ids = [row[0] for row in multiple_overlap_result]
        assert booking_ids == [self.booking_id, new_booking_id]
