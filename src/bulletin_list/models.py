from sqlmodel import SQLModel, Field
from typing import Optional

class BulletinList(SQLModel, table=True):
    __tablename__: str = "bulletin_list"
    id: Optional[int] = Field(default=None, primary_key=True)
    name:str
    href: str
    date: str
    type:str = Field(default=None)