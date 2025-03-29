"""公告列表模块的数据库模型

该模块定义了公告列表相关的数据模型

"""
from sqlmodel import Field, SQLModel
from src.bulletin_list.schemas import BulletinType


class BulletinList(SQLModel, table=True):
    """公告列表数据库模型
    
    存储从网站爬取的公告列表信息
    
    Attributes:
        id (int | None): 主键ID
        name (str): 公告标题
        href (str): 公告链接
        date (str): 公告日期，格式为YYYY-MM-DD
        type (str): 公告类型，对应BulletinType的值
    """
    __tablename__: str = "bulletin_list" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    href: str
    date: str = Field(index=True)
    type: str = Field(default=BulletinType.OTHER.value)