"""APP 的入口

"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException

# 定时任务
from src.task.daily import scheduler,apscheduler_start
# 路由
from src.bulletin.router import router as bulletin_router
from src.dev.router import router as dev_router
from src.auth.router import router as auth_router
# 中间件
from src.utils.http import LoggingMiddleware,setup_cors_middleware,http_exception_wrapper
from src.utils.http import docs_url,redoc_url,openapi_url
# 数据库
from src.database import create_db_and_tables
# 其他工具
from src.logs.service import setup_logging

# 日志配置
setup_logging()
# 生命周期对象
ml_models = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用的生命周期管理
    """
    # Load the ML model
    ml_models["create_db_and_tables"] = create_db_and_tables
    ml_models["apscheduler_start"] = apscheduler_start
    await apscheduler_start()
    yield
    # Clean up the ML models and release resources
    scheduler.shutdown()
    ml_models.clear()

app = FastAPI(
    lifespan=lifespan,
    title="gjoldb API",
    description="gjoldbAPI",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# 添加日志中间件
app.add_middleware(LoggingMiddleware)
# 添加异常处理中间件
app.add_exception_handler(HTTPException, http_exception_wrapper)
# CORS 中间件
setup_cors_middleware(app)

# 路由
app.include_router(bulletin_router, prefix="/bulletins", tags=["公告"])
app.include_router(dev_router, prefix="/dev", tags=["开发"])
app.include_router(auth_router, prefix="/auth", tags=["认证"])



@app.get("/")
async def root():
    """根路由
    """
    return {"message": "Hello Applications!"}
