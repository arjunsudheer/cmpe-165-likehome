import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.db.models import Booking, Status, User, Hotel, HotelRoom, RoomType, Notification
from backend.jobs.bookings import create_booking_reminders
from decimal import Decimal

def _make_hotel(session):
    h = Hotel(name="Test Hotel", price_per_night=Decimal("100.00"), city="San Jose", address="1 Main St")
    session.add(h)
    session.flush()
    return h

def _make_room(session, hotel):
    r = HotelRoom(hotel=hotel.id, room=101, room_type=RoomType.DOUBLE)
    session.add(r)
    session.flush()
    return r

def _auth_headers(client, email="test@example.com"):
    response = client.post(
        "/auth/register",
        json={
            "name": "Tester",
            "email": email,
            "password": "password123",
        },
    )
    if response.status_code == 409:
        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "password123",
            },
        )
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_send_booking_reminders(client, session):
    # Create user with notifications turned on
    user = User(email="reminder@test.com", password="pwd", name="Reminder Test", send_reminder_email=True)
    session.add(user)
    session.commit()
    user_id = user.id

    hotel = _make_hotel(session)
    room = _make_room(session, hotel)

    # Booking starting tomorrow
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    booking = Booking(
        booking_number="REMIND1",
        title="Test Reminder",
        user=user_id,
        room=room.id,
        start_date=tomorrow,
        end_date=tomorrow + timedelta(days=2),
        total_price=200.0,
        status=Status.CONFIRMED
    )
    session.add(booking)
    session.commit()
    booking_id = booking.id

    # Call the job
    # We must patch the engine in jobs/bookings.py so it uses our test session
    import backend.jobs.bookings
    from unittest.mock import patch
    
    with patch("backend.jobs.bookings.Session") as MockSession:
        MockSession.return_value.__enter__.return_value = session
        create_booking_reminders()

    # Check if reminder was marked as created
    session.expire_all()
    b = session.get(Booking, booking_id)
    assert b.reminder_notification_created is True
    
    # Check if Notification was created
    notifications = session.query(Notification).filter_by(user_id=user_id).all()
    assert len(notifications) == 1
    assert "REMIND1" in notifications[0].message

def test_no_reminder_if_disabled(client, session):
    user = User(email="noreminder@test.com", password="pwd", name="No Reminder", send_reminder_email=False)
    session.add(user)
    session.commit()
    user_id = user.id

    hotel = _make_hotel(session)
    room = _make_room(session, hotel)

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    booking = Booking(
        booking_number="REMIND2",
        title="Test No Reminder",
        user=user_id,
        room=room.id,
        start_date=tomorrow,
        end_date=tomorrow + timedelta(days=2),
        total_price=200.0,
        status=Status.CONFIRMED
    )
    session.add(booking)
    session.commit()
    booking_id = booking.id

    from unittest.mock import patch
    with patch("backend.jobs.bookings.Session") as MockSession:
        MockSession.return_value.__enter__.return_value = session
        create_booking_reminders()

    session.expire_all()
    b = session.get(Booking, booking_id)
    assert b.reminder_notification_created is False
    
    notifications = session.query(Notification).filter_by(user_id=user_id).all()
    assert len(notifications) == 0

def test_no_reminder_if_not_tomorrow(client, session):
    user = User(email="faraway@test.com", password="pwd", name="Faraway", send_reminder_email=True)
    session.add(user)
    session.commit()
    user_id = user.id

    hotel = _make_hotel(session)
    room = _make_room(session, hotel)

    # 3 days from now
    future_date = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    booking = Booking(
        booking_number="REMIND3",
        title="Test Future",
        user=user_id,
        room=room.id,
        start_date=future_date,
        end_date=future_date + timedelta(days=2),
        total_price=200.0,
        status=Status.CONFIRMED
    )
    session.add(booking)
    session.commit()
    booking_id = booking.id

    from unittest.mock import patch
    with patch("backend.jobs.bookings.Session") as MockSession:
        MockSession.return_value.__enter__.return_value = session
        create_booking_reminders()

    session.expire_all()
    b = session.get(Booking, booking_id)
    assert b.reminder_notification_created is False
    
    notifications = session.query(Notification).filter_by(user_id=user_id).all()
    assert len(notifications) == 0
