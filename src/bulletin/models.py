from sqlmodel import SQLModel, Field
from typing import Optional
from src.spiders.schemas import BulletinType



class Bulletin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bulletin_date: str
    total_leng: int
    content_total_arr: str
    bulletin_name: Optional[str] = None
    version_id: Optional[int] = Field(default=None, foreign_key="version.id")
    rank_id: int = Field(default=0)
    type: str = Field(default=BulletinType.ROUTINE)


