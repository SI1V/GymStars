from typing import Annotated
from decimal import Decimal
from sqlalchemy.orm import mapped_column


uniq_str = Annotated[str, mapped_column(unique=True)]
auto_pk_int = Annotated[int, mapped_column(init=False, primary_key=True, autoincrement=True)]
str_30 = Annotated[str, 30]
str_50 = Annotated[str, 50]
num_12_4 = Annotated[Decimal, 12]
num_6_2 = Annotated[Decimal, 6]