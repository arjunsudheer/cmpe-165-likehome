"""Idempotent tweaks for existing DB volumes that predate model changes."""

from sqlalchemy import inspect, text

from backend.db.db_connection import engine


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
