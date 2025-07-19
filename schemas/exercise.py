from pydantic import BaseModel
from typing import List, Literal
from pydantic.alias_generators import to_camel
from pydantic.config import ConfigDict
from schemas.rep import RepSchema

class ExerciseSchema(BaseModel):
    id: int
    name: str
    type: Literal["strength", "cardio"]
    reps: List[RepSchema]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)