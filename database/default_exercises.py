from sqlalchemy import select
from database.connection import connection
from models.exercise import Exercise, ExerciseType

# Упражнения по умолчанию
DEFAULT_EXERCISES = [
    {"name": "Приседания со штангой", "type": ExerciseType.STRENGTH},
    {"name": "Жим лёжа", "type": ExerciseType.STRENGTH},
    {"name": "Становая тяга", "type": ExerciseType.STRENGTH},
    {"name": "Беговая дорожка", "type": ExerciseType.CARDIO},
    {"name": "Велотренажёр", "type": ExerciseType.CARDIO},
    {"name": "Скакалка", "type": ExerciseType.CARDIO},
]


@connection
async def init_default_exercises(session):
    existing = await session.scalar(select(Exercise).where(Exercise.is_default == True))
    if existing:
        return

    for data in DEFAULT_EXERCISES:
        exercise = Exercise(
            name=data["name"],
            type=data["type"],
            is_default=True,
            user_id=None,
        )
        session.add(exercise)

    await session.commit()
