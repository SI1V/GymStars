from sqlalchemy.ext.asyncio import AsyncSession
from models.rep import Rep
from typing import List, Dict

async def create_reps(session: AsyncSession, workout_exercise_id: int, reps: List[Dict]) -> None:
    rep_objects = []
    for rep in reps:
        if "duration" in rep:
            # Для кардио упражнений
            rep_objects.append(Rep(
                workout_exercise_id=workout_exercise_id,
                duration=rep["duration"],
                weight=0,
                count=0
            ))
        else:
            # Для силовых упражнений
            rep_objects.append(Rep(
                workout_exercise_id=workout_exercise_id,
                weight=rep["weight"],
                count=rep["count"],
                duration=0
            ))

    session.add_all(rep_objects)
    await session.commit()
