
from sqlmodel import SQLModel, Field
from typing import Optional

class Version(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    start_date: str
    end_date: str
    total: int
    acronyms: str
    fake_version:bool=Field(default=False)
