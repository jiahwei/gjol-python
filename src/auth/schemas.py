"""
认证服务 ORM 对象
"""

from pydantic import BaseModel


class AuthPayload(BaseModel):
    """认证服务的入参类型

    Args:
        BaseModel (_type_): _description_
    """
    id: str = ""
    sig: str = ""