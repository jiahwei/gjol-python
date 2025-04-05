"""公告模块的数据库模型

该模块定义了公告相关的数据模型

"""
from sqlmodel import Field, SQLModel

from src.bulletin_list.schemas import BulletinType


class BulletinDB(SQLModel, table=True):
    """公告数据库模型
    公告数据库模型，用于存储公告相关的数据

    Attributes:
        id: 公告id
        bulletin_date: 公告日期，被方法get_really_bulletin_date处理过的方法，它会把日期格式化成周四
        original_date: 原始公告日期
        total_leng: 公告总长度
        content_total_arr: 公告内容总数组
        bulletin_name: 公告名称
        version_id: 版本id
        type: 公告类型
    """
    __tablename__:str = "bulletin"
    id: int | None = Field(default=None, primary_key=True)
    bulletin_date: str
    original_date: str
    total_leng: int
    content_total_arr: str
    bulletin_name: str | None = None
    version_id: int = Field(foreign_key="version.id")
    type: str = Field(default=BulletinType.ROUTINE.value)


