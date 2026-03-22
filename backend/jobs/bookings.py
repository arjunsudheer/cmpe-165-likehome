from datetime import datetime
from sqlalchemy import update
from sqlalchemy.orm import Session
from backend.db.db_connection import engine
from backend.db.models import Booking, Status

def expire_bookings():
    with Session(engine) as session:
        session.execute(
            update(Booking)
            .where(
                Booking.status == Status.INPROGRESS,
                Booking.expires_at < datetime.now()
            )
            .values(status=Status.CANCELLED)
        )
        session.commit()