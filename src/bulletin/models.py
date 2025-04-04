"""公告模块的数据库模型

该模块定义了公告相关的数据模型

"""
from sqlmodel import Field, SQLModel

from src.bulletin_list.schemas import BulletinType


class BulletinDB(SQLModel, table=True):
    __tablename__:str = "bulletin"
    id: int | None = Field(default=None, primary_key=True)
    bulletin_date: str
    total_leng: int
    content_total_arr: str
    bulletin_name: str | None = None
    version_id: int = Field(foreign_key="version.id")
    rank_id: int = Field(default=0)
    type: str = Field(default=BulletinType.ROUTINE.value)


