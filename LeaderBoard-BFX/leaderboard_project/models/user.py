from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime, timezone

from db.database import Base


class User(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    username = Column(String, nullable=False)
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    current_pnl = Column(Float, default=0.0)
    rank = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
