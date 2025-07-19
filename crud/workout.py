from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from database.session import AsyncSessionLocal
from models.workout import Workout
from schemas.workout import WorkoutCreateSchema, WorkoutUpdateSchema
from typing import List, Optional
from models.workout_exercise import WorkoutExercise


# Получить тренировку по id
async def get_workout_by_id(session: AsyncSessionLocal, workout_id: int) -> Optional[Workout]:
    result = await session.execute(select(Workout).where(Workout.id == workout_id))
    return result.scalar_one_or_none()


async def get_user_workouts(session: AsyncSessionLocal, user_id: int) -> List[Workout]:
    result = await session.execute(
        select(Workout)
        .options(
            selectinload(Workout.exercises).selectinload(WorkoutExercise.exercise)
        )
        .where(Workout.user_id == user_id)
    )
    return result.scalars().all()



# Создать тренировку
async def create_workout(session: AsyncSessionLocal, user_id: int, data: WorkoutCreateSchema) -> Workout:
    workout = Workout(user_id=user_id, date=data.date, comment=data.comment)
    session.add(workout)
    await session.commit()
    await session.refresh(workout)
    return workout

# Обновить тренировку
async def update_workout(session: AsyncSessionLocal, workout_id: int, data: WorkoutUpdateSchema) -> Optional[Workout]:
    stmt = update(Workout).where(Workout.id == workout_id).values(**data.dict(exclude_unset=True)).execution_options(synchronize_session="fetch")
    await session.execute(stmt)
    await session.commit()
    return await get_workout_by_id(session, workout_id)

# Удалить тренировку
async def delete_workout(session: AsyncSessionLocal, workout_id: int) -> None:
    await session.execute(delete(Workout).where(Workout.id == workout_id))
    await session.commit()

# Получить тренировку пользователя по дате
async def get_workout_by_user_and_date(session: AsyncSessionLocal, user_id: int, date) -> Optional[Workout]:
    stmt = (
        select(Workout)
        .where(Workout.user_id == user_id, Workout.date == date)
        .options(
            joinedload(Workout.exercises)
            .joinedload(WorkoutExercise.exercise)
        )
    )
    result = await session.execute(stmt)
    workout = result.unique().scalar_one_or_none()

    if not workout:
        return None

    return workout


async def get_workout_details(session: AsyncSessionLocal, workout: Workout) -> dict:
    """
    Преобразует объект тренировки в словарь с детальной информацией о упражнениях
    """
    # Получаем тренировку со всеми связанными данными в одном запросе
    stmt = (
        select(Workout)
        .where(Workout.id == workout.id)
        .options(
            joinedload(Workout.exercises).joinedload(WorkoutExercise.exercise),
            joinedload(Workout.exercises).joinedload(WorkoutExercise.reps)
        )
    )
    result = await session.execute(stmt)
    workout = result.unique().scalar_one()

    workout_data = {
        "id": workout.id,
        "date": workout.date,
        "user_id": workout.user_id,
        "note": workout.comment,
        "exercises": []
    }

    # Сортируем упражнения по id (порядок добавления)
    sorted_exercises = sorted(workout.exercises, key=lambda x: x.id)

    # Теперь все связанные данные уже загружены
    for we in sorted_exercises:
        exercise = we.exercise
        exercise_data = {
            "id": exercise.id,
            "name": exercise.name,
            "type": exercise.type.value,
            "reps": []
        }

        # Сортируем подходы по id (порядок добавления)
        sorted_reps = sorted(we.reps, key=lambda x: x.id)

        # Используем предзагруженные подходы
        for rep in sorted_reps:
            exercise_data["reps"].append({
                "weight": rep.weight,
                "count": rep.count,
                "duration": rep.duration
            })

        workout_data["exercises"].append(exercise_data)

    return workout_data
