from pydantic import BaseModel
from typing import Optional
from pydantic.alias_generators import to_camel
from pydantic.config import ConfigDict


class RepSchema(BaseModel):
    id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration_minutes: Optional[float] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)
