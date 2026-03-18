import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from models import User, Hotel, HotelRoom, Booking, Review, PointsTransaction
from models import RoomType, Status


# ── Register: User model ──────────────────────────────────────────────


class TestUser:

    def test_create_user(self, session):
        user = User(email="test@example.com", password="hashed_pw")
        session.add(user)
        session.flush()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password == "hashed_pw"

    def test_unique_email(self, session):
        session.add(User(email="dup@example.com", password="pw1"))
        session.flush()

        session.add(User(email="dup@example.com", password="pw2"))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_email_required(self, session):
        session.add(User(password="pw"))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_password_required(self, session):
        session.add(User(email="no_pw@example.com"))
        with pytest.raises(IntegrityError):
            session.flush()


# ── Search: Hotel and HotelRoom models ────────────────────────────────


class TestHotel:

    def test_create_hotel(self, session):
        hotel = Hotel(
            name="Test Hotel",
            price_per_night=Decimal("99.99"),
            city="San Jose",
            address="123 Main St",
        )
        session.add(hotel)
        session.flush()

        assert hotel.id is not None
        assert hotel.name == "Test Hotel"
        assert hotel.city == "San Jose"

    def test_unique_address(self, session):
        session.add(Hotel(
            name="Hotel A",
            price_per_night=Decimal("50.00"),
            city="SF",
            address="456 Elm St",
        ))
        session.flush()

        session.add(Hotel(
            name="Hotel B",
            price_per_night=Decimal("75.00"),
            city="SF",
            address="456 Elm St",
        ))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_default_rating(self, session):
        hotel = Hotel(
            name="Default Rating Hotel",
            price_per_night=Decimal("80.00"),
            city="LA",
            address="789 Oak Ave",
        )
        session.add(hotel)
        session.flush()

        assert hotel.rating == 0

    def test_name_required(self, session):
        session.add(Hotel(
            price_per_night=Decimal("50.00"),
            city="SF",
            address="111 Pine St",
        ))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_price_required(self, session):
        session.add(Hotel(
            name="No Price Hotel",
            city="SF",
            address="222 Pine St",
        ))
        with pytest.raises(IntegrityError):
            session.flush()


class TestHotelRoom:

    def test_create_room(self, session):
        hotel = Hotel(
            name="Room Test Hotel",
            price_per_night=Decimal("100.00"),
            city="NYC",
            address="1 Broadway",
        )
        session.add(hotel)
        session.flush()

        room = HotelRoom(hotel=hotel.id, room=101, room_type=RoomType.SINGLE)
        session.add(room)
        session.flush()

        assert room.id is not None
        assert room.room_type == RoomType.SINGLE

    def test_all_room_types(self, session):
        hotel = Hotel(
            name="Enum Hotel",
            price_per_night=Decimal("100.00"),
            city="NYC",
            address="2 Broadway",
        )
        session.add(hotel)
        session.flush()

        for i, rt in enumerate(RoomType):
            room = HotelRoom(hotel=hotel.id, room=200 + i, room_type=rt)
            session.add(room)
        session.flush()

    def test_hotel_fk_required(self, session):
        session.add(HotelRoom(room=101, room_type=RoomType.SINGLE))
        with pytest.raises(IntegrityError):
            session.flush()


# ── Book: Booking model ───────────────────────────────────────────────


class TestBooking:

    def _make_user_and_room(self, session, suffix=""):
        user = User(email=f"booker{suffix}@example.com", password="pw")
        hotel = Hotel(
            name=f"Booking Hotel{suffix}",
            price_per_night=Decimal("120.00"),
            city="Boston",
            address=f"10 Beacon St{suffix}",
        )
        session.add_all([user, hotel])
        session.flush()

        room = HotelRoom(hotel=hotel.id, room=1, room_type=RoomType.DOUBLE)
        session.add(room)
        session.flush()
        return user, room

    def test_create_booking(self, session):
        user, room = self._make_user_and_room(session)
        booking = Booking(
            title="Weekend Stay",
            user=user.id,
            room=room.id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 3),
            total_price=Decimal("240.00"),
        )
        session.add(booking)
        session.flush()

        assert booking.id is not None
        assert booking.title == "Weekend Stay"
        assert booking.start_date == date(2026, 6, 1)
        assert booking.total_price == Decimal("240.00")

    def test_default_status_confirmed(self, session):
        user, room = self._make_user_and_room(session, suffix="2")
        booking = Booking(
            title="Status Test",
            user=user.id,
            room=room.id,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 2),
            total_price=Decimal("120.00"),
        )
        session.add(booking)
        session.flush()

        assert booking.status == Status.CONFIRMED

    def test_user_fk_required(self, session):
        hotel = Hotel(
            name="FK Hotel",
            price_per_night=Decimal("100.00"),
            city="Denver",
            address="1 Colfax Ave",
        )
        session.add(hotel)
        session.flush()
        room = HotelRoom(hotel=hotel.id, room=1, room_type=RoomType.SINGLE)
        session.add(room)
        session.flush()

        session.add(Booking(
            title="No User",
            room=room.id,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 2),
            total_price=Decimal("100.00"),
        ))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_title_required(self, session):
        user, room = self._make_user_and_room(session, suffix="3")
        session.add(Booking(
            user=user.id,
            room=room.id,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 2),
            total_price=Decimal("100.00"),
        ))
        with pytest.raises(IntegrityError):
            session.flush()


# ── Pay/Rewards: PointsTransaction model ──────────────────────────────


class TestPointsTransaction:

    def test_create_points_transaction(self, session):
        user = User(email="points@example.com", password="pw")
        hotel = Hotel(
            name="Points Hotel",
            price_per_night=Decimal("100.00"),
            city="Seattle",
            address="1 Pike Pl",
        )
        session.add_all([user, hotel])
        session.flush()

        room = HotelRoom(hotel=hotel.id, room=1, room_type=RoomType.SINGLE)
        session.add(room)
        session.flush()

        booking = Booking(
            title="Points Stay",
            user=user.id,
            room=room.id,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 3),
            total_price=Decimal("200.00"),
        )
        session.add(booking)
        session.flush()

        txn = PointsTransaction(
            user_id=user.id,
            booking_id=booking.id,
            points=200,
        )
        session.add(txn)
        session.flush()

        assert txn.id is not None
        assert txn.user_id == user.id
        assert txn.booking_id == booking.id
        assert txn.points == 200

    def test_points_required(self, session):
        user = User(email="no_pts@example.com", password="pw")
        session.add(user)
        session.flush()

        session.add(PointsTransaction(user_id=user.id))
        with pytest.raises(IntegrityError):
            session.flush()


# ── Review model ──────────────────────────────────────────────────────


class TestReview:

    def test_create_review(self, session):
        user = User(email="reviewer@example.com", password="pw")
        hotel = Hotel(
            name="Review Hotel",
            price_per_night=Decimal("90.00"),
            city="Portland",
            address="1 Burnside St",
        )
        session.add_all([user, hotel])
        session.flush()

        review = Review(
            user=user.id,
            hotel=hotel.id,
            title="Great place",
            content="Loved the stay",
            rating=5,
        )
        session.add(review)
        session.flush()

        assert review.id is not None
        assert review.rating == 5

    def test_default_title_and_content(self, session):
        user = User(email="defaults@example.com", password="pw")
        hotel = Hotel(
            name="Defaults Hotel",
            price_per_night=Decimal("70.00"),
            city="Austin",
            address="1 Congress Ave",
        )
        session.add_all([user, hotel])
        session.flush()

        review = Review(user=user.id, hotel=hotel.id, rating=3)
        session.add(review)
        session.flush()

        assert review.title == "No title"
        assert review.content == "No content"

    def test_rating_required(self, session):
        user = User(email="no_rating@example.com", password="pw")
        hotel = Hotel(
            name="No Rating Hotel",
            price_per_night=Decimal("60.00"),
            city="Dallas",
            address="1 Main St Dallas",
        )
        session.add_all([user, hotel])
        session.flush()

        session.add(Review(user=user.id, hotel=hotel.id))
        with pytest.raises(IntegrityError):
            session.flush()

    def test_hotel_fk_required(self, session):
        user = User(email="no_hotel_review@example.com", password="pw")
        session.add(user)
        session.flush()

        session.add(Review(user=user.id, rating=4))
        with pytest.raises(IntegrityError):
            session.flush()
