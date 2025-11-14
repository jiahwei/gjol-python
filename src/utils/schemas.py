"""工具库的schema定义
"""
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")
class Response(BaseModel, Generic[T]):
    """统一封装返回类型
    """
    code: int = 200
    message: str = "OK"
    data: T | None = None

class CreateTokenPayload(BaseModel):
    """创建token的入参类型
    """
    sub: str = ""
    exp: int = 0
    scope: str = ""
