from sqlalchemy import ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Rep(Base):
    __tablename__ = "reps"

    weight: Mapped[float | None] = mapped_column(nullable=True)  # для силовых
    count: Mapped[int | None] = mapped_column(nullable=True)     # для силовых
    duration: Mapped[int | None] = mapped_column(nullable=True)  # для кардио (в минутах)
    workout_exercise_id: Mapped[int] = mapped_column(ForeignKey("workout_exercises.id", ondelete="CASCADE"))

    workout_exercise = relationship("WorkoutExercise", back_populates="reps")
