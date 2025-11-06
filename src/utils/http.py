"""提供http请求的工具函数"""

from typing import TypeVar
import uuid
import os
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from dotenv import load_dotenv

from src.utils.schemas import Response

_ = load_dotenv()
ENV = os.getenv("ENV")
# 根据环境决定是否显示文档
docs_url = None if ENV == "production" else "/docs"
redoc_url = None if ENV == "production" else "/redoc"
openapi_url = None if ENV == "production" else "/openapi.json"

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
    """返回错误的响应"""
    return Response[None](code=code, message=message)


def setup_cors_middleware(app) -> None:
    """按环境为应用注册 CORS 中间件"""
    if ENV == "production":
        origins = [
            "https://gjoldb.info",
            "https://www.gjoldb.info",
        ]
    else:
        origins = ["*"]  # 开发环境允许所有来源

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件,记录请求和响应日志"""

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        http_logger.info(
            "[%s] Start request: %s %s", request_id, request.method, request.url
        )
        response = await call_next(request)
        http_logger.info("[%s] End response: %s", request_id, response.status_code)
        return response


async def http_exception_wrapper(request: Request, exc: HTTPException):
    """HTTP 异常处理中间件
    """
    http_logger.error(
        "[%s] HTTP Exception: %s %s",
        request.state.request_id,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail).model_dump(),
    )
