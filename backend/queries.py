from sqlalchemy import select
from sqlalchemy.orm import Session
from db_connection import engine
from models import User

def get_reward_points(user_id):
    with Session(engine) as session:
        stmt = select(User.points).where(User.id == user_id)
        result = session.execute(stmt)
        return result.scalar_one()