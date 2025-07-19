from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.annotated import str_30
from models.base import Base
from typing import Optional, List
from models.exercise_type import ExerciseType
from models.workout_exercise import WorkoutExercise


class Exercise(Base):
    __tablename__ = "exercises"

    name: Mapped[str_30]
    type: Mapped[ExerciseType]
    is_default: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    owner = relationship("User", back_populates="exercises")

    workout_items: Mapped[List["WorkoutExercise"]] = relationship(back_populates="exercise", cascade="all, delete")
