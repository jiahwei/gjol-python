
from sqlmodel import Field, SQLModel


class Version(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    start_date: str
    end_date: str
    total: int
    acronyms: str
    fake_version:bool=Field(default=False)
