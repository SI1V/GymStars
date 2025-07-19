from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from pydantic.alias_generators import to_camel
from pydantic.config import ConfigDict
from schemas.exercise import ExerciseSchema

class WorkoutCreateSchema(BaseModel):
    date: date
    comment: Optional[str] = None

class WorkoutUpdateSchema(BaseModel):
    date: Optional[date] = None
    comment: Optional[str] = None

class WorkoutSchema(BaseModel):
    id: int
    user_id: int
    date: date
    comment: Optional[str] = None
    exercises: List[ExerciseSchema]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
