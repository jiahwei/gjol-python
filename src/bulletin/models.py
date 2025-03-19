from sqlmodel import SQLModel, Field
from src.bulletin_list.schemas import BulletinType



class Bulletin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    bulletin_date: str
    total_leng: int
    content_total_arr: str
    bulletin_name: str | None = None
    version_id: int | None = Field(default=None, foreign_key="version.id")
    rank_id: int = Field(default=0)
    type: str = Field(default=BulletinType.ROUTINE)


