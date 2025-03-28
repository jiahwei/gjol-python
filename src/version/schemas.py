"""版本模块数据类型
定义了数据传输对象 (DTO)，主要用于 API 接口的请求和响应
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
