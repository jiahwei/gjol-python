"""
认证服务 ORM 对象
"""

from pydantic import BaseModel


class IsOpenManagePayload(BaseModel):
    """认证服务的入参类型

    Args:
        id (str): 加密后的设备ID
        sig (str): 签名
        iv (str): 初始化向量
    """
    id: str = ""
    sig: str = ""
    iv: str = ""
class IsOpenManageResponse(BaseModel):
    """认证服务的出参类型
    """
    isOpenManage: bool = False
    