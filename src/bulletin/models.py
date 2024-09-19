from sqlmodel import SQLModel, Field, create_engine, Session
from typing import Optional

class Bulletin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bulletin_date: str
    total_leng: int
    content_total_arr: str
    bulletin_name: Optional[str] = None
    version_id: Optional[int] = Field(default=None, foreign_key="release.ID")
    order_id: int = Field(default=0)
