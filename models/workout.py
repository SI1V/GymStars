import datetime
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from models.base import Base
from models.workout_exercise import WorkoutExercise


class Workout(Base):
    __tablename__ = "workouts"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    comment: Mapped[Optional[str]]

    user: Mapped["User"] = relationship(back_populates="workouts")
    exercises: Mapped[List["WorkoutExercise"]] = relationship(back_populates="workout", cascade="all, delete")
