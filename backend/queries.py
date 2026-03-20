from sqlalchemy import select, func
from sqlalchemy.orm import Session
from db_connection import engine
from models import User, PointsTransaction
import bcrypt

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


def verify_login(email, password):
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        user = session.execute(stmt).scalar_one_or_none()
        if user is None:
            return {"success": False, "message": "Email not found"}
        if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            return {"success": False, "message": "Incorrect password"}
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user.id
        }