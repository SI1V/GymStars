from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from typing import List


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))

    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship(back_populates="workout_items")
    reps: Mapped[List["Rep"]] = relationship(back_populates="workout_exercise", cascade="all, delete")

