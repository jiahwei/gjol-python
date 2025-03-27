"""版本模块数据类型

"""

from pydantic import BaseModel


class VersionInfo(BaseModel):
    """版本信息

    Attributes:
        version_id (int): 版本ID
        rank (int): 版本排名
    """
    version_id:int
    rank:int
