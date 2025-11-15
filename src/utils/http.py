"""
http相关的工具函数、依赖和中间件
"""

from typing import TypeVar, Annotated
import uuid
import os
import logging
import time
import jwt

from fastapi import HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from dotenv import load_dotenv
from src.utils.schemas import Response, CreateTokenPayload

_ = load_dotenv()
ENV = os.getenv("ENV")
_JWT_SECRET = os.getenv("JWT_SECRET")
if not _JWT_SECRET:
    raise ValueError("JWT_SECRET must be set in the environment variables")
JWT_SECRET: str = _JWT_SECRET
raw_devices = os.getenv("MANAGED_DEVICES", "")
MANAGED_DEVICES = set[str](device.strip() for device in raw_devices.split(",") if device.strip())

security = HTTPBearer()
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

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        http_logger.info(
            "[%s] Start request: %s %s", request_id, request.method, request.url
        )
        try:
            response = await call_next(request)
        except Exception:
            http_logger.exception("[%s] Exception during request handling", request_id)
            raise
        http_logger.info("[%s] End response: %s", request_id, response.status_code)
        response.headers["X-Request-ID"] = request_id
        return response


async def http_exception_wrapper(request: Request, exc: Exception):
    """HTTP 异常处理中间件
    """
    if not isinstance(exc, HTTPException):
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    http_logger.error(
        "[%s] HTTP Exception: %s %s",
        request_id,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, str(exc.detail)).model_dump(),
        headers={"X-Request-ID": request_id},
    )


def creat_token(device_id: str) -> str:
    """创建token"""
    payload_model = CreateTokenPayload(
        sub=device_id, exp=int(time.time()) + 3600, scope="manage"
    )
    payload: dict[str, int | str] = payload_model.model_dump()
    return str(jwt.encode(payload, JWT_SECRET, algorithm="HS256"))

def creat_refresh_token(device_id: str) -> str:
    """创建refresh_token"""
    payload_model = CreateTokenPayload(
        sub=device_id, exp=int(time.time()) + 60 * 60 * 24 * 30, scope="refresh"
    )
    payload: dict[str, int | str] = payload_model.model_dump()
    return str(jwt.encode(payload, JWT_SECRET, algorithm="HS256"))

def create_tokens(device_id: str) -> dict[str, str]:
    """创建token和refresh_token"""
    return {
        "token": creat_token(device_id),
        "refreshToken": creat_refresh_token(device_id),
    }

def verify_token(token: str) -> CreateTokenPayload:
    """验证token"""
    payload: dict[str, int | str] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return CreateTokenPayload.model_validate(payload)

def verify_refresh_token(token: str) -> CreateTokenPayload:
    """验证refresh_token"""
    payload: dict[str, int | str] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return CreateTokenPayload.model_validate(payload)

def get_current_refresh_device(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """用refersh_token 刷新token时的依赖"""
    token = credentials.credentials
    try:
        data = verify_refresh_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="RefreshToken已过期") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="RefreshToken无效") from exc

    if data.scope != "refresh":
        raise HTTPException(status_code=403, detail="权限不足")
    if not data.sub:
        raise HTTPException(status_code=400, detail="Token缺少设备标识")
    if data.sub not in MANAGED_DEVICES:
        raise HTTPException(status_code=403, detail="设备未授权")
    return data.sub


def get_current_device(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    """设备认证依赖 - 验证Token并检查设备授权状态"""
    token = credentials.credentials
    try:
        data = verify_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token已过期") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Token无效") from exc

    if data.scope != "manage":
        raise HTTPException(status_code=403, detail="权限不足")

    if not data.sub:
        raise HTTPException(status_code=400, detail="Token缺少设备标识")
    if data.sub not in MANAGED_DEVICES:
        raise HTTPException(status_code=403, detail="设备未授权")
    return data.sub
