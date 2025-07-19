from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.exercise import Exercise
from models.exercise import ExerciseType



async def get_user_exercises(session: AsyncSession, user_id: int):
    stmt = select(Exercise).where(
        (Exercise.user_id == user_id) | (Exercise.is_default == True)
    ).order_by(Exercise.name)

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_user_exercises_paginated(session: AsyncSession, user_id: int, offset: int = 0, limit: int = 5):
    stmt = (
        select(Exercise)
        .where((Exercise.user_id == user_id) | (Exercise.is_default == True))
        .order_by(Exercise.name)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    exercises = result.scalars().all()

    count_stmt = (
        select(Exercise.id)
        .where((Exercise.user_id == user_id) | (Exercise.is_default == True))
    )
    total_result = await session.execute(count_stmt)
    total = len(total_result.scalars().all())

    return exercises, total


async def get_exercises_by_type(session, exercise_type: str, user_id: int, page: int, page_size: int):
    offset = page * page_size
    enum_type = ExerciseType[exercise_type.upper()]
    stmt = (
        select(Exercise)
        .where(
            Exercise.type == enum_type,
            or_(Exercise.user_id == user_id, Exercise.is_default == True)
        )
        .offset(offset)
        .limit(page_size)
    )

    count_stmt = (
        select(Exercise)
        .where(
            Exercise.type == enum_type,
            or_(Exercise.user_id == user_id, Exercise.is_default == True)
        )
    )

    result = await session.execute(stmt)
    total_result = await session.execute(count_stmt)
    total = len(total_result.scalars().all())
    return result.scalars().all(), total


async def create_exercise(
    session: AsyncSession,
    name: str,
    description: str,
    ex_type: str,
    user_id: int,
    is_default: bool = False,
) -> Exercise:
    try:
        ex_type_enum = ExerciseType[ex_type.upper()]
    except KeyError:
        raise ValueError(f"Недопустимый тип упражнения: {ex_type}")

    exercise = Exercise(
        name=name,
        type=ex_type_enum,
        user_id=user_id,
        is_default=is_default
    )
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise

async def get_exercise_by_id(session: AsyncSession, ex_id: int) -> Exercise | None:
    stmt = select(Exercise).where(Exercise.id == ex_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_exercise_by_name(session: AsyncSession, exercise_id: int, new_name: str) -> Exercise:
    exercise = await session.get(Exercise, exercise_id)
    if exercise is None:
        raise ValueError(f"Упражнение с ID {exercise_id} не найдено.")

    exercise.name = new_name
    await session.commit()
    await session.refresh(exercise)
    return exercise

async def delete_exercise(session: AsyncSession, ex_id: int, user_id: int):
    stmt = delete(Exercise).where(
        Exercise.id == ex_id,
        Exercise.user_id == user_id,
        Exercise.is_default.is_(False)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount

    await session.commit()
