from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from typing import List
from models.rep import Rep


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"))

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workout_items")

    reps: Mapped[List["Rep"]] = relationship(back_populates="workout_exercise", cascade="all, delete")

