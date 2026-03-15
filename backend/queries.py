from sqlalchemy import select, func
from sqlalchemy.orm import Session
from db_connection import engine
from models import User, PointsTransaction


def get_reward_points(user_id):
    with Session(engine) as session:
        stmt = select(User.points).where(User.id == user_id)
        result = session.execute(stmt)
        return result.scalar_one()


def get_points_history(user_id):
    with Session(engine) as session:
        stmt = (
            select(PointsTransaction)
            .where(PointsTransaction.user_id == user_id)
            .order_by(PointsTransaction.recorded_at.desc())
        )
        return session.execute(stmt).scalars().all()
