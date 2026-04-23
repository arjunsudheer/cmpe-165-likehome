"""Idempotent tweaks for existing DB volumes that predate model changes."""

from sqlalchemy import inspect, text

from backend.db.db_connection import engine
from backend.db.models import Base, Notification
def ensure_points_transactions_log_column() -> None:
    """
    Older deployments created `points_transactions` without a `log` column.
    SQLAlchemy create_all() does not ALTER tables, so we add the column here.
    """
    insp = inspect(engine)
    if not insp.has_table("points_transactions"):
        return
    cols = {c["name"] for c in insp.get_columns("points_transactions")}
    if "log" in cols:
        return

    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "postgresql":
            conn.execute(
                text(
                    "ALTER TABLE points_transactions "
                    "ADD COLUMN log VARCHAR(100) NOT NULL DEFAULT ''"
                )
            )
            conn.execute(
                text("ALTER TABLE points_transactions ALTER COLUMN log DROP DEFAULT")
            )
        else:
            # SQLite and others: keep a default so existing rows stay valid.
            conn.execute(
                text(
                    "ALTER TABLE points_transactions "
                    "ADD COLUMN log VARCHAR(100) NOT NULL DEFAULT ''"
                )
            )


def ensure_reminder_email_columns() -> None:
    """
    Add `send_reminder_email` to `users` and `reminder_email_sent` to `bookings`.
    """
    insp = inspect(engine)
    if not insp.has_table("users"):
        return

    users_cols = {c["name"] for c in insp.get_columns("users")}
    bookings_cols = {c["name"] for c in insp.get_columns("bookings")}

    dialect = engine.dialect.name
    with engine.begin() as conn:
        if "send_reminder_email" not in users_cols:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN send_reminder_email BOOLEAN DEFAULT TRUE"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN send_reminder_email BOOLEAN DEFAULT 1"))
        
        if "reminder_email_sent" not in bookings_cols:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE bookings ADD COLUMN reminder_email_sent BOOLEAN DEFAULT FALSE"))
            else:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN reminder_email_sent BOOLEAN DEFAULT 0"))

def ensure_notifications_table() -> None:
    """
    Create notifications table if it doesn't exist, and add reminder_notification_created to bookings.
    """
    insp = inspect(engine)
    if not insp.has_table("notifications"):
        Base.metadata.create_all(engine, tables=[Notification.__table__])

    if not insp.has_table("bookings"):
        return

    bookings_cols = {c["name"] for c in insp.get_columns("bookings")}
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if "reminder_notification_created" not in bookings_cols:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE bookings ADD COLUMN reminder_notification_created BOOLEAN DEFAULT FALSE"))
            else:
                conn.execute(text("ALTER TABLE bookings ADD COLUMN reminder_notification_created BOOLEAN DEFAULT 0"))
