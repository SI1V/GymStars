from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from typing import List
from models.exercise import Exercise
from models.workout import Workout


class User(Base):
    __tablename__ = "users"

    username: Mapped[str | None] = mapped_column(nullable=True)
    full_name: Mapped[str | None] = mapped_column(nullable=True)
    is_subscribed: Mapped[bool] = mapped_column(default=False)
    subscription_expires: Mapped[datetime | None] = mapped_column(nullable=True)

    exercises: Mapped[List["Exercise"]] = relationship(back_populates="owner", cascade="all, delete")
    workouts: Mapped[List["Workout"]] = relationship(back_populates="user", cascade="all, delete")
