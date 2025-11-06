"""提供http请求的工具函数"""

from typing import TypeVar
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.schemas import Response


T = TypeVar("T")
http_logger = logging.getLogger("http")


def success_response(data: T | None = None) -> Response[T]:
    """返回成功的响应

    Args:
        data (T | None, optional): 响应数据. Defaults to None.

    Returns:
        Response[T]: 成功的响应
    """
    return Response[T](data=data)


def error_response(code: int, message: str) -> Response[None]:
    """返回错误的响应

    Args:
        code (int): 错误码
        message (str): 错误信息

    Returns:
        Response[None]: 错误的响应
    """
    return Response[None](code=code, message=message)


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件,记录请求和响应日志"""
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        http_logger.info(
            "[%s] Start request: %s %s", request_id, request.method, request.url
        )
        response = await call_next(request)
        http_logger.info(
            "[%s] End response: %s", request_id, response.status_code
        )
        return response
