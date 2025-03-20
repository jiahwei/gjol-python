from sqlmodel import SQLModel, Field

class BulletinList(SQLModel, table=True):
    __tablename__: str = "bulletin_list" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    name:str
    href: str
    date: str
    type:str = Field(default=None)