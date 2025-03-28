"""版本模块的数据库模型

该模块定义了版本相关的数据模型，用于管理游戏版本信息。

"""

from sqlmodel import Field, SQLModel


class Version(SQLModel, table=True):
    """版本数据库模型

    该类定义了版本的数据模型，包括版本名称、起止时间、总数、缩写等属性。

    Attributes:
        id (int | None): 版本的唯一标识符，默认为None。
        name (str): 版本的名称。
        start_date (str): 版本的起始日期。
        end_date (str): 版本的结束日期。
        total (int): 版本的总数量。
        acronyms (str): 版本的缩写。
        fake_version (bool): 版本是否为寰宇会，默认为False。
    """
    id: int | None = Field(default=None, primary_key=True)
    name: str
    start_date: str
    end_date: str
    total: int
    acronyms: str
    fake_version:bool=Field(default=False)
